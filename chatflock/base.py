from typing import Any, Callable, List, Optional, Sequence, TypeVar

import abc
import dataclasses
from datetime import datetime

from pydantic import BaseModel, Field

from chatflock.errors import (
    ChatParticipantAlreadyJoinedToChatError,
    ChatParticipantNotJoinedToChatError,
    NotEnoughActiveParticipantsInChatError,
)

TOutputSchema = TypeVar("TOutputSchema", bound=BaseModel)


class ChatParticipant(abc.ABC):
    name: str

    def __init__(self, name: str):
        self.name = name

    def on_new_chat_message(self, chat: "Chat", message: "ChatMessage") -> None:
        pass

    def on_chat_started(self, chat: "Chat") -> None:
        pass

    def on_chat_ended(self, chat: "Chat") -> None:
        pass

    def on_participant_joined_chat(self, chat: "Chat", participant: "ChatParticipant") -> None:
        pass

    def on_participant_left_chat(self, chat: "Chat", participant: "ChatParticipant") -> None:
        pass

    def __str__(self) -> str:
        return self.name

    def detailed_str(self, level: int = 0) -> str:
        prefix = "    " * level
        return f"{prefix}Name: {self.name}"


class ActiveChatParticipant(ChatParticipant):
    symbol: str
    messages_hidden: bool = False

    def __init__(self, name: str, symbol: str = "👤", messages_hidden: bool = False):
        super().__init__(name=name)

        self.symbol = symbol
        self.messages_hidden = messages_hidden

    @abc.abstractmethod
    def respond_to_chat(self, chat: "Chat") -> str:
        raise NotImplementedError()

    def __str__(self) -> str:
        return f"{self.symbol} {self.name}"

    def detailed_str(self, level: int = 0) -> str:
        prefix = "    " * level
        return f"{prefix}- Name: {self.name}\n{prefix}  Symbol: {self.symbol}"


class ChatMessage(BaseModel):
    id: int
    sender_name: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatConductor(abc.ABC):
    @abc.abstractmethod
    def select_next_speaker(self, chat: "Chat") -> Optional[ActiveChatParticipant]:
        raise NotImplementedError()

    def get_chat_result(self, chat: "Chat") -> str:
        messages = chat.get_messages()
        if len(messages) == 0:
            return ""

        last_message = messages[-1]

        return last_message.content

    def prepare_chat(self, chat: "Chat", **kwargs: Any) -> None:
        pass

    def initiate_dialog(
        self,
        chat: "Chat",
        initial_message: Optional[str] = None,
        from_participant: Optional[ChatParticipant] = None,
        **kwargs: Any,
    ) -> str:
        self.prepare_chat(chat=chat, **kwargs)

        active_participants = chat.get_active_participants()
        if len(active_participants) <= 0:
            raise NotEnoughActiveParticipantsInChatError(len(active_participants))

        self.start_chat(chat=chat)

        if initial_message is not None:
            if from_participant is None:
                from_participant = active_participants[0]

            chat.add_message(sender_name=from_participant.name, content=initial_message)

        next_speaker = self.select_next_speaker(chat=chat)
        while next_speaker is not None:
            messages = chat.get_messages()
            if chat.max_total_messages is not None and len(messages) >= chat.max_total_messages:
                break

            try:
                message_content = next_speaker.respond_to_chat(chat=chat)
            except KeyboardInterrupt:
                if next_speaker.name == "User":
                    raise

                user_participant = chat.get_active_participant_by_name("User")
                if user_participant is None:
                    raise

                message_content = user_participant.respond_to_chat(chat=chat)

            chat.add_message(sender_name=next_speaker.name, content=message_content)

            next_speaker = self.select_next_speaker(chat=chat)

        self.end_chat(chat=chat)

        return self.get_chat_result(chat=chat)

    def start_chat(self, chat: "Chat") -> None:
        active_participants = chat.backing_store.get_active_participants()
        non_active_participants = chat.backing_store.get_non_active_participants()
        all_participants = active_participants + non_active_participants

        for participant in all_participants:
            participant.on_chat_started(chat=chat)

    def end_chat(self, chat: "Chat") -> None:
        active_participants = chat.backing_store.get_active_participants()
        non_active_participants = chat.backing_store.get_non_active_participants()
        all_participants = active_participants + non_active_participants

        for participant in all_participants:
            participant.on_chat_ended(chat=chat)


class ChatDataBackingStore(abc.ABC):
    @abc.abstractmethod
    def get_messages(self) -> List[ChatMessage]:
        raise NotImplementedError()

    @abc.abstractmethod
    def add_message(self, sender_name: str, content: str, timestamp: Optional[datetime] = None) -> ChatMessage:
        raise NotImplementedError()

    @abc.abstractmethod
    def clear_messages(self) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_active_participants(self) -> List[ActiveChatParticipant]:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_non_active_participants(self) -> List[ChatParticipant]:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_active_participant_by_name(self, name: str) -> Optional[ActiveChatParticipant]:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_non_active_participant_by_name(self, name: str) -> Optional[ChatParticipant]:
        raise NotImplementedError()

    @abc.abstractmethod
    def add_participant(self, participant: ChatParticipant) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def remove_participant(self, participant: ChatParticipant) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def has_active_participant_with_name(self, participant_name: str) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def has_non_active_participant_with_name(self, participant_name: str) -> bool:
        raise NotImplementedError()


class ChatRenderer(abc.ABC):
    def render_new_chat_message(self, chat: "Chat", message: ChatMessage) -> None:
        raise NotImplementedError()


@dataclasses.dataclass
class GeneratedChatComposition:
    participants: Sequence[ChatParticipant]
    participants_interaction_schema: str


class ChatCompositionGenerator(abc.ABC):
    @abc.abstractmethod
    def generate_composition_for_chat(
        self,
        chat: "Chat",
        goal: str,
        composition_suggestion: Optional[str] = None,
        interaction_schema: Optional[str] = None,
    ) -> GeneratedChatComposition:
        raise NotImplementedError()


class Chat:
    backing_store: ChatDataBackingStore
    renderer: ChatRenderer
    name: Optional[str] = None
    max_total_messages: Optional[int] = None
    hide_messages: bool = False

    def __init__(
        self,
        backing_store: ChatDataBackingStore,
        renderer: ChatRenderer,
        initial_participants: Optional[Sequence[ChatParticipant]] = None,
        name: Optional[str] = None,
        max_total_messages: Optional[int] = None,
        hide_messages: bool = False,
    ):
        if max_total_messages is not None and max_total_messages <= 0:
            raise ValueError("Max total messages must be None or greater than 0.")

        self.backing_store = backing_store
        self.renderer = renderer
        self.name = name
        self.hide_messages = hide_messages
        self.max_total_messages = max_total_messages

        for i, participant in enumerate(initial_participants or []):
            self.add_participant(participant)

    def add_participant(self, participant: ChatParticipant) -> None:
        if self.has_active_participant_with_name(participant.name) or self.has_non_active_participant_with_name(
            participant.name
        ):
            raise ChatParticipantAlreadyJoinedToChatError(participant.name)

        self.backing_store.add_participant(participant)

        all_participants = (
            self.backing_store.get_active_participants() + self.backing_store.get_non_active_participants()
        )
        for participant in all_participants:
            participant.on_participant_joined_chat(chat=self, participant=participant)

    def remove_participant(self, participant: ChatParticipant) -> None:
        self.backing_store.remove_participant(participant)

        active_participants = self.backing_store.get_active_participants()
        non_active_participants = self.backing_store.get_non_active_participants()
        all_participants = active_participants + non_active_participants

        for participant in all_participants:
            participant.on_participant_left_chat(chat=self, participant=participant)

    def add_message(self, sender_name: str, content: str) -> None:
        sender = self.backing_store.get_active_participant_by_name(sender_name)
        if sender is None:
            raise ChatParticipantNotJoinedToChatError(sender_name)

        message = self.backing_store.add_message(sender_name=sender_name, content=content)

        self.renderer.render_new_chat_message(chat=self, message=message)

        active_participants = self.backing_store.get_active_participants()
        non_active_participants = self.backing_store.get_non_active_participants()
        all_participants = active_participants + non_active_participants

        for participant in all_participants:
            participant.on_new_chat_message(chat=self, message=message)

    def get_messages(self) -> List[ChatMessage]:
        return self.backing_store.get_messages()

    def clear_messages(self):
        self.backing_store.clear_messages()

    def get_active_participants(self) -> List[ActiveChatParticipant]:
        return self.backing_store.get_active_participants()

    def get_non_active_participants(self) -> List[ChatParticipant]:
        return self.backing_store.get_non_active_participants()

    def get_active_participant_by_name(self, name: str) -> Optional[ActiveChatParticipant]:
        return self.backing_store.get_active_participant_by_name(name=name)

    def get_non_active_participant_by_name(self, name: str) -> Optional[ChatParticipant]:
        return self.backing_store.get_non_active_participant_by_name(name=name)

    def has_active_participant_with_name(self, participant_name: str) -> bool:
        return self.backing_store.has_active_participant_with_name(participant_name=participant_name)

    def has_non_active_participant_with_name(self, participant_name: str) -> bool:
        return self.backing_store.has_non_active_participant_with_name(participant_name=participant_name)

    @property
    def active_participants_str(self):
        return "\n\n".join([participant.detailed_str() for participant in self.get_active_participants()])
