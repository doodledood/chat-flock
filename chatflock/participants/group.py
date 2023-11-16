from typing import Any, Optional

from halo import Halo

from chatflock.base import ActiveChatParticipant, Chat, ChatConductor
from chatflock.structured_string import Section, StructuredString
from chatflock.use_cases.request_response import get_response


class GroupBasedChatParticipant(ActiveChatParticipant):
    inner_chat_conductor: ChatConductor
    inner_chat: Chat
    mission: str
    spinner: Optional[Halo] = None
    clear_inner_chat_before_responding: bool = False

    def __init__(
        self,
        group_name: str,
        chat: Chat,
        mission: str,
        chat_conductor: ChatConductor,
        clear_inner_chat_before_responding: bool = False,
        spinner: Optional[Halo] = None,
        **kwargs: Any,
    ) -> None:
        self.inner_chat = chat
        self.inner_chat_conductor = chat_conductor
        self.clear_inner_chat_before_responding = clear_inner_chat_before_responding
        self.mission = mission
        self.spinner = spinner

        # Make sure the inner chat is aligned
        self.inner_chat.name = group_name

        super().__init__(name=group_name, **kwargs)

        # Make sure the chat & conductor are initialized, as it may be a dynamic chat with
        # no participants yet.
        self.inner_chat_conductor.prepare_chat(chat=self.inner_chat)

    def respond_to_chat(self, chat: "Chat") -> str:
        if self.clear_inner_chat_before_responding:
            self.inner_chat.clear_messages()

        prev_spinner_text = None
        if self.spinner is not None:
            prev_spinner_text = self.spinner.text
            self.spinner.stop_and_persist(symbol="👥", text=f"{self.name} started a discussion.")
            self.spinner.start(text=f"{self.name} is discussing...")

        messages = chat.get_messages()
        conversation_str = "\n".join([f"- {message.sender_name}: {message.content}" for message in messages])

        leader = self.inner_chat.get_active_participants()[0]
        request_for_group, _ = get_response(
            query="Please translate the request for yourself in the external conversation into a collaboration "
            "request for your internal group. This is the external conversation:"
            f"\n```{conversation_str}```\n\nThe group should understand exactly what to discuss, what to "
            "decide on, and how to respond back based on this. ",
            answerer=leader,
        )
        group_response = self.inner_chat_conductor.initiate_dialog(
            chat=self.inner_chat, initial_message=request_for_group
        )

        if self.spinner is not None:
            self.spinner.succeed(text=f"{self.name} concluded their discussion.")
            if prev_spinner_text is not None:
                self.spinner.start(text=prev_spinner_text)
        messages = self.inner_chat.get_messages()
        group_response_conversation_str = "\n".join(
            [f"- {message.sender_name}: {message.content}" for message in messages]
        )
        leader_response_back, _ = get_response(
            query=str(
                StructuredString(
                    sections=[
                        Section(name="External Conversation", text=conversation_str),
                        Section(name="Internal Group Conversation", text=group_response_conversation_str),
                        Section(
                            name="Task",
                            text="You are a part of the EXTERNAL CONVERSATION and need to respond back. "
                            "You and your group have collaborated on a response back for the "
                            "EXTERNAL CONVERSATION. Please transform the INTERNAL GROUP CONVERSATION into "
                            "a proper, in-context response back (in your name) for the EXTERNAL CONVERSATION; "
                            "it should be mainly based on the conclusion of the internal conversation. "
                            "Your response will be sent to the EXTERNAL CONVERSATION verbatim.",
                        ),
                    ]
                )
            ),
            answerer=leader,
        )

        return leader_response_back

    def __str__(self) -> str:
        active_participants = self.inner_chat.get_active_participants()

        if len(active_participants) > 0:
            names = [str(p) for p in active_participants]
            return f'{self.name} (Includes: {", ".join(names)})'

        return self.name

    def detailed_str(self, level: int = 0) -> str:
        prefix = "    " * level
        participants = self.inner_chat.get_active_participants()
        members_str = "\n\n".join([p.detailed_str(level=level + 1) for p in participants])

        return (
            f'{prefix}- Name: {self.name}\n{prefix}  Symbol: {self.symbol}\n{prefix}  Mission: "{self.mission}"'
            f"\n{members_str}"
        )
