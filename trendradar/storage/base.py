"""订阅条目与采集结果。"""
from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class RSSItem:
    """RSS 条目数据模型"""

    title: str                          # 标题
    feed_id: str                        # RSS 源 ID（如 "hacker-news"）
    feed_name: str = ""                 # RSS 源名称（运行时使用）
    url: str = ""                       # 文章链接
    guid: str = ""                      # GUID/ID（RSS guid 或 Atom id）
    published_at: str = ""              # RSS 发布时间（ISO 格式）
    summary: str = ""                   # 摘要/描述
    author: str = ""                    # 作者
    crawl_time: str = ""                # 抓取时间（HH:MM 格式）

    # 统计信息
    first_time: str = ""                # 首次抓取时间
    last_time: str = ""                 # 最后抓取时间
    count: int = 1                      # 抓取次数

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "title": self.title,
            "feed_id": self.feed_id,
            "feed_name": self.feed_name,
            "url": self.url,
            "published_at": self.published_at,
            "summary": self.summary,
            "author": self.author,
            "crawl_time": self.crawl_time,
            "first_time": self.first_time,
            "last_time": self.last_time,
            "count": self.count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RSSItem":
        """从字典创建"""
        return cls(
            title=data.get("title", ""),
            feed_id=data.get("feed_id", ""),
            feed_name=data.get("feed_name", ""),
            url=data.get("url", ""),
            published_at=data.get("published_at", ""),
            summary=data.get("summary", ""),
            author=data.get("author", ""),
            crawl_time=data.get("crawl_time", ""),
            first_time=data.get("first_time", ""),
            last_time=data.get("last_time", ""),
            count=data.get("count", 1),
        )


@dataclass
class RSSData:
    """
    RSS 数据集合

    结构:
    - date: 日期（YYYY-MM-DD）
    - crawl_time: 抓取时间（HH:MM）
    - items: 按 feed_id 分组的 RSS 条目
    - id_to_name: feed_id 到名称的映射
    - failed_ids: 失败的 feed_id 列表
    """

    date: str                                   # 日期
    crawl_time: str                             # 抓取时间
    items: Dict[str, List[RSSItem]]             # 按 feed_id 分组的条目
    id_to_name: Dict[str, str] = field(default_factory=dict)   # ID到名称映射
    failed_ids: List[str] = field(default_factory=list)        # 失败的ID

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        items_dict = {}
        for feed_id, rss_list in self.items.items():
            items_dict[feed_id] = [item.to_dict() for item in rss_list]

        return {
            "date": self.date,
            "crawl_time": self.crawl_time,
            "items": items_dict,
            "id_to_name": self.id_to_name,
            "failed_ids": self.failed_ids,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RSSData":
        """从字典创建"""
        items = {}
        items_data = data.get("items", {})
        for feed_id, rss_list in items_data.items():
            items[feed_id] = [RSSItem.from_dict(item) for item in rss_list]

        return cls(
            date=data.get("date", ""),
            crawl_time=data.get("crawl_time", ""),
            items=items,
            id_to_name=data.get("id_to_name", {}),
            failed_ids=data.get("failed_ids", []),
        )

    def get_total_count(self) -> int:
        """获取条目总数"""
        return sum(len(rss_list) for rss_list in self.items.values())
