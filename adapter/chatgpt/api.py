from typing import Generator, Union

import asyncio
import janus
from loguru import logger

from adapter.botservice import BotAdapter
from revChatGPT.V3 import Chatbot as OpenAIChatbot

from config import OpenAIAPIKey
from constants import botManager


class ChatGPTAPIAdapter(BotAdapter):
    api_info: OpenAIAPIKey = None
    """API Key"""

    bot: OpenAIChatbot = None
    """实例"""

    def __init__(self, session_id: str = "unknown"):
        self.session_id = session_id
        self.api_info = botManager.pick('openai-api')
        self.bot = OpenAIChatbot(api_key=self.api_info.api_key, proxy=self.api_info.proxy)
        self.conversation_id = None
        self.parent_id = None
        super().__init__()

    async def rollback(self):
        if len(self.bot.conversation) > 0:
            self.bot.rollback()
            return True
        else:
            return False

    async def on_reset(self):
        self.bot.conversation = []
        self.api_info = botManager.pick('openai-api')
        self.bot = OpenAIChatbot(api_key=self.api_info.api_key, proxy=self.api_info.proxy)

    def ask_sync(self, sync_q, prompt):
        try:
            for resp in self.bot.ask_stream(prompt):
                sync_q.put(resp)
            sync_q.put(None)
        except Exception as e:
            sync_q.put(e)
        sync_q.join()

    async def ask(self, prompt: str) -> Generator[str, None, None]:
        full_response = ''
        queue: janus.Queue[Union[str, Exception, None]] = janus.Queue()
        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(None, self.ask_sync, queue.sync_q, prompt)
        while not queue.async_q.closed:
            resp = await queue.async_q.get()
            queue.async_q.task_done()
            if isinstance(resp, Exception):
                # 出现了错误
                raise resp
            elif resp is None:
                # 发完了
                break
            full_response += resp
            yield full_response
        await future
        queue.close()
        await queue.wait_closed()
        logger.debug("[ChatGPT-API] 响应：" + full_response)

    async def preset_ask(self, role: str, text: str):
        if role.endswith('bot') or role == 'chatgpt':
            logger.debug(f"[预设] 响应：{text}")
            yield text
            role = 'assistant'
        if role not in ['assistant', 'user', 'system']:
            raise ValueError(f"预设文本有误！仅支持设定 assistant、user 或 system 的预设文本，但你写了{role}。")
        self.bot.conversation.append({"role": role, "content": text})
