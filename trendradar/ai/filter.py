"""根据固定工程主题及个人兴趣对订阅条目分类。"""
import json
from typing import List, Dict, Optional
from trendradar.ai.client import AIClient
from trendradar.ai.prompt_loader import load_prompt_template


class AIFilter:
    def __init__(self, ai_config, filter_config, get_time_func, debug=False):
        self.client = AIClient(ai_config)
        self.batch_size = filter_config.get('BATCH_SIZE', 20)
        self.debug = debug
        self.classify_system, self.classify_user = load_prompt_template('prompt.txt', 'ai_filter', 'AI筛选')

    def classify_batch(
        self,
        titles: List[Dict],
        tags: List[Dict],
        interests_content: str = "",
    ) -> Optional[List[Dict]]:
        """
        阶段 B：对一批新闻标题做分类

        Args:
            titles: [{"id": news_item_id, "title": str, "source": str}]
            tags: [{"id": tag_id, "tag": str, "description": str}]
            interests_content: 用户的兴趣描述（含质量过滤要求）

        Returns:
            成功返回 [{"news_item_id": int, "tag_id": int, "relevance_score": float}, ...]（无匹配时为空列表）；
            调用失败返回 None（用于区分"无匹配"与"调用失败"，失败批次不标记已分析以便下次重试）
        """
        if not titles or not tags:
            return []

        if not self.classify_user:
            print("[AI筛选] 分类提示词模板为空")
            return None

        # 构建标签列表文本
        tags_list = "\n".join(
            f"{t['id']}. {t['tag']}: {t.get('description', '')}"
            for t in tags
        )

        # 构建新闻列表文本
        news_list = "\n".join(
            f"{t['id']}. [{t.get('source', '')}] {t['title']}"
            + (f" | RSS摘要（非全文）:{t['summary'][:500]}" if t.get("summary") else "")
            for t in titles
        )

        # 填充模板
        user_prompt = self.classify_user
        user_prompt = user_prompt.replace("{interests_content}", interests_content)
        user_prompt = user_prompt.replace("{tags_list}", tags_list)
        user_prompt = user_prompt.replace("{news_count}", str(len(titles)))
        user_prompt = user_prompt.replace("{news_list}", news_list)

        messages = []
        if self.classify_system:
            messages.append({"role": "system", "content": self.classify_system})
        messages.append({"role": "user", "content": user_prompt})

        if self.debug:
            print(f"\n[AI筛选][DEBUG] === 分类 Prompt (标题数={len(titles)}, 标签={len(tags)}) ===")
            for m in messages:
                role = m['role']
                content = m['content']
                # 截断过长的新闻列表：只显示前5条和后5条
                lines = content.split('\n')
                # 找到新闻列表区域并截断
                if len(lines) > 30:
                    # 显示前15行 + 省略提示 + 后10行
                    head = lines[:15]
                    tail = lines[-10:]
                    omitted = len(lines) - 25
                    truncated = '\n'.join(head) + f'\n... (省略 {omitted} 行) ...\n' + '\n'.join(tail)
                    print(f"[{role}]\n{truncated}")
                else:
                    print(f"[{role}]\n{content}")
            print(f"[AI筛选][DEBUG] === Prompt 结束 (长度: {sum(len(m['content']) for m in messages)} 字符) ===")

        try:
            response = self.client.chat(messages)

            return self._parse_classify_response(response, titles, tags)
        except Exception as e:
            print(f"[AI筛选] 分类请求失败: {type(e).__name__}: {e}")
            return None

    def _parse_classify_response(
        self,
        response: str,
        titles: List[Dict],
        tags: List[Dict],
    ) -> Optional[List[Dict]]:
        """解析分类的 AI 响应

        支持两种 JSON 格式：
        - 新格式（扁平）: [{"id": 1, "tag_id": 1, "score": 0.9}, ...]
        - 旧格式（嵌套）: [{"id": 1, "tags": [{"tag_id": 1, "score": 0.9}]}, ...]

        每条新闻只保留一个最高分的 tag，杜绝同一条出现在多个标签下。
        """
        json_str = self._extract_json(response)
        if not json_str:
            if self.debug:
                print(f"[AI筛选][DEBUG] 无法从分类响应中提取 JSON，原始响应前 500 字符: {(response or '')[:500]}")
            return None

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            if self.debug:
                print(f"[AI筛选][DEBUG] 分类响应 JSON 解析失败: {e}")
                print(f"[AI筛选][DEBUG] 提取的 JSON 文本前 500 字符: {json_str[:500]}")
            return None

        if not isinstance(data, list):
            if self.debug:
                print(f"[AI筛选][DEBUG] 分类响应顶层不是数组，实际类型: {type(data).__name__}")
            return None

        # 构建 id 映射
        title_ids = {t["id"] for t in titles}
        title_map = {t["id"]: t["title"] for t in titles}
        tag_id_set = {t["id"] for t in tags}
        tag_name_map = {t["id"]: t["tag"] for t in tags}

        # 每条新闻只保留一个最高分的 tag
        best_per_news: Dict[int, Dict] = {}  # news_id -> {"tag_id": ..., "score": ...}
        skipped_news_ids = 0
        skipped_tag_ids = 0
        skipped_empty = 0

        for item in data:
            if not isinstance(item, dict):
                continue
            news_id = item.get("id")
            if news_id not in title_ids:
                skipped_news_ids += 1
                continue

            # 收集此条新闻的所有候选 tag
            candidates = []

            if "tag_id" in item:
                # 新格式（扁平）: {"id": 1, "tag_id": 1, "score": 0.9}
                candidates.append({"tag_id": item["tag_id"], "score": item.get("score", 0.5)})
            elif "tags" in item:
                # 旧格式（嵌套）: {"id": 1, "tags": [{"tag_id": 1, "score": 0.9}]}
                matched_tags = item.get("tags", [])
                if isinstance(matched_tags, list):
                    if not matched_tags:
                        skipped_empty += 1
                        continue
                    candidates.extend(matched_tags)

            if not candidates:
                skipped_empty += 1
                continue

            # 取最高分的有效 tag
            best_tag_id = None
            best_score = -1.0

            for tag_match in candidates:
                if not isinstance(tag_match, dict):
                    continue
                tag_id = tag_match.get("tag_id")
                if tag_id not in tag_id_set:
                    skipped_tag_ids += 1
                    continue

                score = tag_match.get("score", 0.5)
                try:
                    score = float(score)
                    score = max(0.0, min(1.0, score))
                except (ValueError, TypeError):
                    score = 0.5

                if score > best_score:
                    best_score = score
                    best_tag_id = tag_id

            if best_tag_id is not None:
                # 如果同一条新闻被多次返回，只保留分数更高的
                existing = best_per_news.get(news_id)
                if existing is None or best_score > existing["relevance_score"]:
                    best_per_news[news_id] = {
                        "news_item_id": news_id,
                        "tag_id": best_tag_id,
                        "relevance_score": best_score,
                    }

        results = list(best_per_news.values())

        if self.debug:
            ai_returned = len(data)
            print(f"[AI筛选][DEBUG] --- 分类解析结果 ---")
            print(f"[AI筛选][DEBUG] AI 返回 {ai_returned} 条, 有效 {len(results)} 条 (每条新闻仅保留最高分 tag)")
            if skipped_empty > 0:
                print(f"[AI筛选][DEBUG] 跳过空 tags: {skipped_empty} 条")
            if skipped_news_ids > 0:
                print(f"[AI筛选][DEBUG] !! 跳过无效 news_id: {skipped_news_ids} 条")
            if skipped_tag_ids > 0:
                print(f"[AI筛选][DEBUG] !! 跳过无效 tag_id: {skipped_tag_ids} 条")

            # 按标签汇总
            tag_summary: Dict[int, List[str]] = {}
            for r in results:
                tid = r["tag_id"]
                if tid not in tag_summary:
                    tag_summary[tid] = []
                tag_summary[tid].append(
                    f"  [{r['news_item_id']}] {title_map.get(r['news_item_id'], '?')[:40]} (score={r['relevance_score']:.2f})"
                )

            for tid, items in tag_summary.items():
                tname = tag_name_map.get(tid, f"tag_{tid}")
                print(f"[AI筛选][DEBUG] 标签「{tname}」匹配 {len(items)} 条:")
                for line in items:
                    print(line)

        return results

    def _extract_json(self, response: str) -> Optional[str]:
        """从 AI 响应中提取 JSON 字符串"""
        if not response or not response.strip():
            return None

        json_str = response.strip()

        if "```json" in json_str:
            parts = json_str.split("```json", 1)
            if len(parts) > 1:
                code_block = parts[1]
                end_idx = code_block.find("```")
                json_str = code_block[:end_idx] if end_idx != -1 else code_block
        elif "```" in json_str:
            parts = json_str.split("```", 2)
            if len(parts) >= 2:
                json_str = parts[1]

        json_str = json_str.strip()
        return json_str if json_str else None
