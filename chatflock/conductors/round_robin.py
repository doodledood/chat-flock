from typing import Optional

from chatflock.base import ActiveChatParticipant, Chat, ChatConductor, ChatMessage
from chatflock.errors import ChatParticipantNotJoinedToChatError


class RoundRobinChatConductor(ChatConductor):
    def select_next_speaker(self, chat: Chat) -> Optional[ActiveChatParticipant]:
        active_participants = chat.get_active_participants()
        if len(active_participants) <= 0:
            return None

        messages = chat.get_messages()
        last_message = messages[-1] if len(messages) > 0 else None

        if last_message is not None and self.is_termination_message(last_message):
            return None

        last_speaker = last_message.sender_name if last_message is not None else None
        if last_speaker is None:
            return next(iter(active_participants))

        # Rotate to the next participant in the list.
        participant_names = [participant.name for participant in active_participants]

        if last_speaker not in participant_names:
            next_speaker_name = participant_names[0]
        else:
            last_speaker_index = participant_names.index(last_speaker)
            next_speaker_index = (last_speaker_index + 1) % len(participant_names)
            next_speaker_name = participant_names[next_speaker_index]

        next_speaker = chat.get_active_participant_by_name(next_speaker_name)
        if next_speaker is None or not isinstance(next_speaker, ActiveChatParticipant):
            raise ChatParticipantNotJoinedToChatError(next_speaker_name)

        return next_speaker

    def get_chat_result(self, chat: "Chat") -> str:
        result = super().get_chat_result(chat=chat)

        try:
            idx = result.rindex("TERMINATE")
            result = result[:idx].strip()
        except ValueError:
            result = result.strip()

        return result

    def is_termination_message(self, message: ChatMessage) -> bool:
        return message.content.strip().endswith("TERMINATE")
