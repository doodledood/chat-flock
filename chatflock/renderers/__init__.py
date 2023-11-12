from chatflock.base import ChatRenderer, Chat, ChatMessage
from .terminal import TerminalChatRenderer


class NoChatRenderer(ChatRenderer):
    def render_new_chat_message(self, chat: Chat, message: ChatMessage):
        pass
