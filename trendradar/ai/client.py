# coding=utf-8
"""
AI 客户端模块

基于 LiteLLM 的统一 AI 模型接口
支持 100+ AI 提供商（OpenAI、DeepSeek、Gemini、Claude、国内模型等）
"""

import os
from typing import Any, Dict, List

from litellm import completion


class AIClient:
    """统一的 AI 客户端（基于 LiteLLM）"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 AI 客户端

        Args:
            config: AI 配置字典
                - MODEL: 模型标识（格式: provider/model_name）
                - API_KEY: API 密钥
                - API_BASE: API 基础 URL（可选）
                - TEMPERATURE: 采样温度
                - MAX_TOKENS: 最大生成 token 数
                - TIMEOUT: 请求超时时间（秒）
                - NUM_RETRIES: 重试次数（可选）
                - FALLBACK_MODELS: 备用模型列表（可选）
                - EXTRA_PARAMS: 透传给 LiteLLM 的额外参数（可选），如
                  extra_headers、top_p、presence_penalty、stop 等
        """
        self.model = config.get("MODEL", "deepseek/deepseek-chat")
        self.api_key = config.get("API_KEY") or os.environ.get("AI_API_KEY", "")
        self.api_base = config.get("API_BASE", "")
        self.temperature = config.get("TEMPERATURE", 1.0)
        self.max_tokens = config.get("MAX_TOKENS", 5000)
        self.timeout = config.get("TIMEOUT", 120)
        self.num_retries = config.get("NUM_RETRIES", 2)
        self.fallback_models = config.get("FALLBACK_MODELS", [])
        # config.yaml 中 ai.extra_params 的透传参数（如自定义请求头）
        self.extra_params = config.get("EXTRA_PARAMS") or {}
        if not isinstance(self.extra_params, dict):
            print(
                f"[AI] 配置错误: ai.extra_params 应为字典，"
                f"当前为 {type(self.extra_params).__name__}，已忽略"
            )
            self.extra_params = {}

    def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        调用 AI 模型进行对话

        Args:
            messages: 消息列表，格式: [{"role": "system/user/assistant", "content": "..."}]
            **kwargs: 额外参数，会覆盖默认配置

        Returns:
            str: AI 响应内容

        Raises:
            Exception: API 调用失败时抛出异常
        """
        # 构建请求参数
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "timeout": kwargs.get("timeout", self.timeout),
            "num_retries": kwargs.get("num_retries", self.num_retries),
        }

        # 添加 API Key
        if self.api_key:
            params["api_key"] = self.api_key

        # 添加 API Base（如果配置了）
        if self.api_base:
            params["api_base"] = self.api_base

        # 添加 max_tokens（如果配置了且不为 0）
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        if max_tokens and max_tokens > 0:
            params["max_tokens"] = max_tokens

        # 添加 fallback 模型（如果配置了）
        if self.fallback_models:
            params["fallbacks"] = self.fallback_models

        # 合并配置文件中的 extra_params（如自定义请求头 extra_headers），
        # 再用调用方 kwargs 覆盖；两者均不覆盖上方已确定的核心参数，
        # 因此未配置 extra_params 时行为与原先完全一致
        for key, value in {**self.extra_params, **kwargs}.items():
            if key not in params:
                params[key] = value

        # LiteLLM retries transport/provider errors, but an HTTP-success response
        # with no answer needs separate, bounded handling. Never use reasoning as
        # the answer, and never log provider bodies or request credentials.
        retries = min(2, max(0, int(params['num_retries'])))
        for attempt in range(retries + 1):
            response = completion(**params)
            choices = getattr(response, 'choices', None) or []
            choice = choices[0] if choices else None
            message = getattr(choice, 'message', None)
            content = getattr(message, 'content', None)
            if isinstance(content, list):
                content = "\n".join(
                    item.get('text', '') for item in content
                    if isinstance(item, dict) and item.get('type', 'text') in ('text', 'output_text')
                    and isinstance(item.get('text'), str)
                )
            if isinstance(content, str) and content.strip():
                return content

            finish = getattr(choice, 'finish_reason', None)
            # Only known protocol values are safe diagnostic output.
            if finish not in ('stop', 'length', 'content_filter', 'tool_calls', 'function_call'):
                finish = 'unknown'
            usage = getattr(response, 'usage', None)
            tokens = getattr(usage, 'completion_tokens', None)
            token_label = str(tokens) if isinstance(tokens, int) else 'unknown'
            details = f'finish_reason={finish}, completion_tokens={token_label}'
            # Refusals and tool-only responses cannot be repaired by blind retry.
            if finish in ('content_filter', 'tool_calls', 'function_call') or attempt == retries:
                raise RuntimeError(f'AI 返回空响应（{details}，已尝试 {attempt + 1} 次）')
            print(f'[AI] 正文为空（{details}），重试 {attempt + 1}/{retries}')

    def validate_config(self) -> tuple[bool, str]:
        """
        验证配置是否有效

        Returns:
            tuple: (是否有效, 错误信息)
        """
        if not self.model:
            return False, "未配置 AI 模型（model）"

        if not self.api_key:
            return False, "未配置 AI API Key，请在 config.yaml 或环境变量 AI_API_KEY 中设置"

        # 验证模型格式（应该包含 provider/model）
        if "/" not in self.model:
            return False, f"模型格式错误: {self.model}，应为 'provider/model' 格式（如 'deepseek/deepseek-chat'）"

        return True, ""
