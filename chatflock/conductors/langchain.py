from typing import Any, Dict, List, Optional, Sequence

from halo import Halo
from langchain.chat_models.base import BaseChatModel
from langchain.schema import AIMessage, BaseMessage, BaseRetriever, Document, HumanMessage, SystemMessage
from langchain.tools import BaseTool

from chatflock.ai_utils import execute_chat_model_messages
from chatflock.base import ActiveChatParticipant, Chat, ChatCompositionGenerator, ChatConductor, ChatMessage
from chatflock.errors import ChatParticipantNotJoinedToChatError
from chatflock.structured_string import Section, StructuredString


class LangChainBasedAIChatConductor(ChatConductor):
    default_termination_condition: str = f"""Terminate the chat on the following conditions:
    - When the goal of the chat has been achieved
    - If one of the participants asks you to terminate it or has finished their sentence with "TERMINATE"."""

    def __init__(
        self,
        chat_model: BaseChatModel,
        composition_generator: Optional[ChatCompositionGenerator] = None,
        participants_interaction_schema: Optional[str] = None,
        termination_condition: Optional[str] = None,
        retriever: Optional[BaseRetriever] = None,
        spinner: Optional[Halo] = None,
        tools: Optional[List[BaseTool]] = None,
        chat_model_args: Optional[Dict[str, Any]] = None,
    ):
        self.chat_model = chat_model
        self.chat_model_args = chat_model_args or {}
        self.tools = tools
        self.retriever = retriever
        self.composition_generator = composition_generator
        self.participants_interaction_schema = participants_interaction_schema
        self.termination_condition = termination_condition or self.default_termination_condition
        self.spinner = spinner

        self.composition_initialized = False

    def create_next_speaker_system_prompt(self, chat: "Chat") -> str:
        chat_messages = chat.get_messages()

        if self.retriever is not None and len(chat_messages) > 0:
            relevant_docs = self.get_relevant_docs(messages=chat_messages)
        else:
            relevant_docs = []

        system_message = StructuredString(
            sections=[
                Section(
                    name="Mission",
                    text="Select the next speaker in the conversation based on the previous messages in the "
                    "conversation and an optional SPEAKER INTERACTION SCHEMA. If it seems to you that the chat "
                    "should end instead of selecting a next speaker, terminate it.",
                ),
                Section(name="Rules", list=["You can only select one of the participants in the group chat."]),
                Section(
                    name="Process",
                    list=[
                        "Look at the last message in the conversation and determine who should speak next based on the "
                        "SPEAKER INTERACTION SCHEMA, if provided.",
                        "If based on TERMINATION CONDITION you determine that the chat should end, you should return the "
                        "string TERMINATE instead of a participant name.",
                    ],
                ),
                Section(
                    name="Input",
                    list=[
                        "Chat goal",
                        "Currently active participants in the conversation" "Speaker interaction schema",
                        "Previous messages from the conversation",
                    ],
                ),
                Section(
                    name="Output",
                    text="The name of the next speaker in the conversation. Or, TERMINATE if the chat should end, "
                    "instead.",
                ),
                Section(name="Example Outputs", list=['"John"', '"TERMINATE"']),
                Section(
                    name="Additional Context for Selection",
                    text="None"
                    if len(relevant_docs) == 0
                    else "The following documents may be relevant for your selection of the "
                    "next speaker, only use them for context for a better response, "
                    "if applicable",
                    sub_sections=[
                        Section(name=f"Document {i + 1}", text=f"```{doc.page_content}```")
                        for i, doc in enumerate(relevant_docs)
                    ],
                ),
            ]
        )

        return str(system_message)

    def create_next_speaker_first_human_prompt(self, chat: "Chat") -> str:
        messages = chat.get_messages()
        messages_list = [f"- {message.sender_name}: {message.content}" for message in messages]

        participants = chat.get_active_participants()

        prompt = StructuredString(
            sections=[
                Section(name="Chat Goal", text=chat.goal or "No explicit chat goal provided."),
                Section(
                    name="Currently Active Participants", list=[f"{str(participant)}" for participant in participants]
                ),
                Section(
                    name="Speaker Interaction Schema",
                    text=self.participants_interaction_schema or "Not provided. Use your best judgement.",
                ),
                Section(name="Termination Condition", text=self.termination_condition),
                Section(
                    name="Chat Messages",
                    text="No messages yet." if len(messages_list) == 0 else None,
                    list=messages_list if len(messages_list) > 0 else [],
                ),
            ]
        )

        return str(prompt)

    def prepare_chat(self, chat: "Chat", **kwargs: Any) -> None:
        # If a composition generator is provided, generate a new composition for the chat before starting.
        if self.composition_generator is not None and not self.composition_initialized:
            composition_suggestion = kwargs.get("composition_suggestion", None)
            new_composition = self.composition_generator.generate_composition_for_chat(
                chat=chat,
                composition_suggestion=composition_suggestion,
                participants_interaction_schema=self.participants_interaction_schema,
                termination_condition=self.termination_condition,
            )

            # Sync participants with the new composition.
            current_active_participants = chat.get_active_participants()
            new_participants_names = {p.name for p in new_composition.participants}

            for participant in new_composition.participants:
                # Add missing participants.
                if not chat.has_active_participant_with_name(participant.name):
                    chat.add_participant(participant)
                    continue

                # Remove other participants not mentioned in the new composition.
                if participant.name not in new_participants_names:
                    chat.remove_participant(participant)

            self.participants_interaction_schema = new_composition.participants_interaction_schema
            self.termination_condition = new_composition.termination_condition

            self.composition_initialized = True

        super().prepare_chat(chat=chat, **kwargs)

    def select_next_speaker(self, chat: Chat) -> Optional[ActiveChatParticipant]:
        participants = chat.get_active_participants()
        if len(participants) <= 1:
            return None

        if self.spinner is not None:
            if chat.name is None:
                self.spinner.start(text="The Chat Conductor is selecting the next speaker...")
            else:
                self.spinner.start(text=f"The Chat Conductor ({chat.name}) is selecting the next speaker...")

        # Ask the AI to select the next speaker.
        messages = [
            SystemMessage(content=self.create_next_speaker_system_prompt(chat=chat)),
            HumanMessage(content=self.create_next_speaker_first_human_prompt(chat=chat)),
        ]

        result = self.execute_messages(messages=messages)
        next_speaker_name = result.strip()

        while not chat.has_active_participant_with_name(next_speaker_name) and next_speaker_name != "TERMINATE":
            messages.append(AIMessage(content=next_speaker_name))
            messages.append(
                HumanMessage(
                    content=f'Speaker "{next_speaker_name}" is not a participant in the chat. Choose another one.'
                )
            )

            result = self.execute_messages(messages=messages)
            next_speaker_name = result.strip()

        if next_speaker_name == "TERMINATE":
            if self.spinner is not None:
                if chat.name is None:
                    self.spinner.stop_and_persist(
                        symbol="👥", text="The Chat Conductor has decided to terminate the chat."
                    )
                else:
                    self.spinner.stop_and_persist(
                        symbol="👥", text=f"The Chat Conductor ({chat.name}) has decided to terminate the " f"chat."
                    )

            return None

        next_speaker = chat.get_active_participant_by_name(next_speaker_name)
        if next_speaker is None:
            raise ChatParticipantNotJoinedToChatError(next_speaker_name)

        if self.spinner is not None:
            if chat.name is None:
                self.spinner.succeed(
                    text=f'The Chat Conductor has selected "{str(next_speaker)}" ' f"as the next speaker."
                )
            else:
                self.spinner.succeed(
                    text=f'The Chat Conductor ({chat.name}) has selected "{str(next_speaker)}" ' f"as the next speaker."
                )

        return next_speaker

    def execute_messages(self, messages: Sequence[BaseMessage]) -> str:
        return execute_chat_model_messages(
            messages=messages,
            chat_model=self.chat_model,
            tools=self.tools,
            spinner=self.spinner,
            chat_model_args=self.chat_model_args,
        )

    def get_relevant_docs(self, messages: Sequence[ChatMessage]) -> List[Document]:
        if self.retriever is None:
            return []

        return self.retriever.get_relevant_documents(query=messages[-1].content)
