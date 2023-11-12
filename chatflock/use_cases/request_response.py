from typing import Optional, Tuple

from chatflock.backing_stores import InMemoryChatDataBackingStore
from chatflock.base import ActiveChatParticipant, Chat, ChatDataBackingStore, ChatRenderer
from chatflock.conductors import RoundRobinChatConductor
from chatflock.participants.user import UserChatParticipant
from chatflock.renderers import NoChatRenderer


def get_response(query: str, answerer: ActiveChatParticipant,
                 backing_store: Optional[ChatDataBackingStore] = None,
                 renderer: Optional[ChatRenderer] = None) -> Tuple[str, Chat]:
    user = UserChatParticipant(name='User')
    participants = [user, answerer]

    chat = Chat(
        backing_store=backing_store or InMemoryChatDataBackingStore(),
        renderer=renderer or NoChatRenderer(),
        initial_participants=participants,
        max_total_messages=2
    )

    chat_conductor = RoundRobinChatConductor()
    answer = chat_conductor.initiate_chat_with_result(chat=chat, initial_message=query, from_participant=user)

    return answer, chat
