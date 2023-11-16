from typing import Any

from chatflock.base import ActiveChatParticipant, Chat


class UserChatParticipant(ActiveChatParticipant):
    def __init__(self, name: str = "User", role: str = "User", symbol: str = "👤", **kwargs: Any):
        super().__init__(name, messages_hidden=True, **kwargs)

        self.role = role
        self.symbol = symbol

    def respond_to_chat(self, chat: Chat) -> str:
        return input(f"{self.symbol} ({self.name}): ")

    def __str__(self) -> str:
        return f"{self.symbol} {self.name} ({self.role})"

    def detailed_str(self, level: int = 0) -> str:
        prefix = "    " * level
        return f"{prefix}- Name: {self.name}\n{prefix}  Role: {self.role}\n{prefix}  Symbol: {self.symbol}"
