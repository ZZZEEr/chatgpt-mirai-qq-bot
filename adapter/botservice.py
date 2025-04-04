from typing import Generator


class BotAdapter:
    """定义所有 Chatbot 的通用接口"""
    preset_name: str = "default"
    def __init__(self, session_id: str = "unknown"): ...

    async def ask(self, msg: str) -> Generator[str, None, None]: ...
    """向 AI 发送消息"""

    async def rollback(self): ...
    """回滚对话"""

    async def on_reset(self): ...
    """当会话被重置时，此函数被调用"""

    async def preset_ask(self, role: str, text: str): ...
    """以预设方式进行提问"""
