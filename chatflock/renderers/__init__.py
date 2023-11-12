from chatflock.base import Chat, ChatMessage, ChatRenderer

from .terminal import TerminalChatRenderer


class NoChatRenderer(ChatRenderer):
    def render_new_chat_message(self, chat: Chat, message: ChatMessage) -> None:
        pass


__all__ = ["TerminalChatRenderer", "NoChatRenderer"]
