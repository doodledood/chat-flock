from typing import Any, Dict, List, Optional, Sequence

from halo import Halo
from langchain.chat_models.base import BaseChatModel
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.tools import BaseTool

from chatflock.ai_utils import execute_chat_model_messages
from chatflock.backing_stores import InMemoryChatDataBackingStore
from chatflock.base import ActiveChatParticipant, Chat, ChatCompositionGenerator, GeneratedChatComposition
from chatflock.composition_generators import ManageParticipantsOutputSchema
from chatflock.conductors import LangChainBasedAIChatConductor
from chatflock.parsing_utils import string_output_to_pydantic
from chatflock.participants.internal_group import InternalGroupBasedChatParticipant
from chatflock.participants.langchain import LangChainBasedAIChatParticipant
from chatflock.renderers import TerminalChatRenderer
from chatflock.structured_string import Section, StructuredString


class LangChainBasedAIChatCompositionGenerator(ChatCompositionGenerator):
    def __init__(
        self,
        chat_model: BaseChatModel,
        generator_tools: Optional[List[BaseTool]] = None,
        participant_available_tools: Optional[List[BaseTool]] = None,
        chat_model_args: Optional[Dict[str, Any]] = None,
        spinner: Optional[Halo] = None,
        n_output_parsing_tries: int = 3,
        prefer_critics: bool = False,
        generate_composition_extra_args: Optional[Dict[str, Any]] = None,
    ):
        self.chat_model = chat_model
        self.chat_model_args = chat_model_args or {}
        self.generator_tools = generator_tools
        self.participant_available_tools = participant_available_tools
        self.spinner = spinner
        self.n_output_parsing_tries = n_output_parsing_tries
        self.prefer_critics = prefer_critics
        self.generate_composition_extra_args = generate_composition_extra_args or {}

        self.participant_tool_names_to_tools = {tool.name: tool for tool in self.participant_available_tools or []}

    def generate_composition_for_chat(
        self,
        chat: Chat,
        composition_suggestion: Optional[str] = None,
        participants_interaction_schema: Optional[str] = None,
        termination_condition: Optional[str] = None,
    ) -> GeneratedChatComposition:
        if composition_suggestion is None:
            composition_suggestion = self.generate_composition_extra_args.get("composition_suggestion", None)

        if participants_interaction_schema is None:
            participants_interaction_schema = self.generate_composition_extra_args.get(
                "participants_interaction_schema", None
            )

        if termination_condition is None:
            termination_condition = self.generate_composition_extra_args.get("termination_condition", None)

        create_internal_chat = self.generate_composition_extra_args.get("create_internal_chat", None)
        if create_internal_chat is None:

            def create_internal_chat(**kwargs: Any) -> Chat:
                return Chat(
                    name=kwargs.get("name", None),
                    goal=kwargs.get("goal", None),
                    backing_store=InMemoryChatDataBackingStore(),
                    renderer=TerminalChatRenderer(),
                )

        if self.spinner is not None:
            self.spinner.start(text="The Chat Composition Generator is creating a new chat composition...")

        # Ask the AI to select the next speaker.
        messages = [
            SystemMessage(content=self.create_compose_chat_participants_system_prompt(chat=chat)),
            HumanMessage(
                content=self.create_compose_chat_participants_first_human_prompt(
                    chat=chat,
                    participant_available_tools=self.participant_available_tools,
                    composition_suggestion=composition_suggestion,
                    participants_interaction_schema=participants_interaction_schema,
                    termination_condition=termination_condition,
                )
            ),
        ]

        result = self.execute_messages(messages=messages)

        output = string_output_to_pydantic(
            output=result,
            chat_model=self.chat_model,
            output_schema=ManageParticipantsOutputSchema,
            n_tries=self.n_output_parsing_tries,
            spinner=self.spinner,
            hide_message=False,
        )

        participants_to_add_names = [str(participant) for participant in output.participants_to_add]
        participants_to_remove_names = [participant_name for participant_name in output.participants_to_remove]

        if self.spinner is not None:
            name = "The Chat Composition Generator"
            if chat.name is not None:
                name = f"{name} ({chat.name})"

            if len(output.participants_to_remove) == 0 and len(output.participants_to_add) == 0:
                self.spinner.succeed(text=f"{name} has decided to keep the current chat composition.")
            elif len(output.participants_to_remove) > 0 and len(output.participants_to_add) == 0:
                self.spinner.succeed(
                    text=f"{name} has decided to remove the following participants: "
                    f'{", ".join(participants_to_remove_names)}'
                )
            elif len(output.participants_to_remove) == 0 and len(output.participants_to_add) > 0:
                self.spinner.succeed(
                    text=f"{name} has decided to add the following participants: "
                    f'{", ".join(participants_to_add_names)}'
                )
            else:
                self.spinner.succeed(
                    text=f"{name} has decided to remove the following participants: "
                    f'{", ".join(participants_to_remove_names)} and add the following participants: '
                    f'{", ".join(participants_to_add_names)}'
                )

        participants: List[ActiveChatParticipant] = [
            p for p in chat.get_active_participants() if p.name not in output.participants_to_remove
        ]

        for participant in output.participants_to_add:
            if participant.type == "individual":
                participant_tools: List[BaseTool] = [
                    self.participant_tool_names_to_tools[tool_name]
                    for tool_name in participant.tools or []
                    if tool_name in self.participant_tool_names_to_tools
                ]
                chat_participant: ActiveChatParticipant = LangChainBasedAIChatParticipant(
                    name=participant.name,
                    role=participant.role,
                    personal_mission=participant.mission,
                    tools=participant_tools,
                    symbol=participant.symbol,
                    chat_model=self.chat_model,
                    spinner=self.spinner,
                    chat_model_args=self.chat_model_args,
                )
            else:
                chat_participant = InternalGroupBasedChatParticipant(
                    group_name=participant.name,
                    mission=participant.mission,
                    chat=create_internal_chat(
                        name=participant.name if chat.name is None else f"{chat.name} > {participant.name}",
                        goal=participant.mission,
                    ),
                    chat_conductor=LangChainBasedAIChatConductor(
                        chat_model=self.chat_model,
                        chat_model_args=self.chat_model_args,
                        spinner=self.spinner,
                        composition_generator=LangChainBasedAIChatCompositionGenerator(
                            chat_model=self.chat_model,
                            chat_model_args=self.chat_model_args,
                            spinner=self.spinner,
                            n_output_parsing_tries=self.n_output_parsing_tries,
                            generate_composition_extra_args=dict(
                                composition_suggestion=participant.composition_suggestion
                            ),
                        ),
                    ),
                    spinner=self.spinner,
                )

            participants.append(chat_participant)

        return GeneratedChatComposition(
            participants=participants,
            participants_interaction_schema=output.updated_speaker_interaction_schema,
            termination_condition=output.updated_termination_condition,
        )

    def create_compose_chat_participants_system_prompt(self, chat: "Chat") -> str:
        active_participants = chat.get_active_participants()

        adding_participants = [
            "Add participants based on their potential contribution to the goal.",
            "You can either add individual participants or entire teams."
            'If you add an individual participant, generate a name, role (succinct title like "Writer", "Developer", '
            "etc.), and personal mission for each new participant such that they can contribute to the goal the best "
            "they can, each in their complementary own way.",
            "If you add a team, generate a name, and a mission for the team, in the same way.",
            "Always try to add or complete a comprehensive composition of participants that have "
            "orthogonal and complementary specialties, skills, roles, and missions (whether they are teams or "
            "individuals). You may not necessarily have the option to change this composition later, so make sure "
            "you summon the right participants.",
        ]

        if self.prefer_critics:
            adding_participants.append(
                "Since most participants you summon will not be the best experts in the world, even though they think "
                "they are, they will be to be overseen. For that, most tasks will require at least 2 experts, "
                "one doing a task and the other that will act as a critic to that expert; they can loop back and "
                "forth and iterate on a better answer. For example, instead of having a Planner only, have a Planner "
                "and a Plan Critic participants to have this synergy. You can skip critics for the most trivial tasks."
            )

        system_message = StructuredString(
            sections=[
                Section(
                    name="Mission",
                    text="Evaluate the chat conversation based on the INPUT. "
                    "Make decisions about adding or removing participants based on their potential contribution "
                    "towards achieving the goal. Update the interaction schema and the termination condition "
                    "to reflect changes in participants and the goal.",
                ),
                Section(
                    name="Process",
                    list=[
                        "Think about the ideal composition of participants that can contribute to the goal in a "
                        "step-by-step manner by looking at all the inputs.",
                        "Assess if the current participants are sufficient for ideally contributing to the goal.",
                        "If insufficient, summon additional participants (or teams) as needed.",
                        "If some participants (individuals or teams) are unnecessary, remove them.",
                        "Update the interaction schema and termination condition to accommodate changes in "
                        "participants.",
                    ],
                    list_item_prefix=None,
                ),
                Section(
                    name="Participants Composition",
                    sub_sections=[
                        Section(
                            name="Adding Participants",
                            list=adding_participants,
                            sub_sections=[
                                Section(
                                    name="Team-based Participants",
                                    list=[
                                        "For very difficult tasks, you may need to summon a team (as a participant) "
                                        "instead of an individual to work together to achieve a sub-goal, similar to "
                                        "actual companies of people.",
                                        "This team will contain a group of internal individual (or even sub-teams) "
                                        "participants. Do not worry about the team's composition at this point.",
                                        "Include a team name, mission, and a composition suggestion for the members of "
                                        "the team (could be individuals or more teams again). Ensure the suggestion "
                                        "contains an indication of whether a participant is an individual or a team. "
                                        'Format like: "Name: ...\nMission: ...\nComposition Suggestion: '
                                        'NAME (individual), NAME (individual), NAME (Team), NAME (Team)..."',
                                    ],
                                ),
                                Section(
                                    name="Naming Individual Participants",
                                    list=[
                                        "Generate a creative name that fits the role and mission.",
                                        "You can use play on words, stereotypes, or any other way you want to be "
                                        "original.",
                                        'For example: "CEO" -> "Maximilian Power", "CTO" -> "Nova Innovatus"',
                                    ],
                                ),
                                Section(
                                    name="Naming Team-based Participants",
                                    list=[
                                        "In contrast to individual participants, you should name teams based only on "
                                        "their mission and composition. Do not be creative here.",
                                        'For example: "Development Team", "Marketing Team"',
                                    ],
                                ),
                                Section(
                                    name="Giving Tools to Participants",
                                    list=[
                                        "Only individual participants can be given tools.",
                                        "You must only choose a tool from the AVAILABLE PARTICIPANT TOOLS list.",
                                        "A tools should be given to a participant only if it can help them fulfill "
                                        "their personal mission better.",
                                    ],
                                ),
                                Section(
                                    name="Correct Hierarchical Composition",
                                    list=[
                                        "If you add a team, make sure to add the team as a participant, and not its "
                                        "individual members."
                                    ],
                                ),
                            ],
                        ),
                        Section(
                            name="Removing Participants",
                            list=[
                                "Remove participants only if they cannot contribute to the goal or fit into the "
                                "interaction schema.Ignore past performance. Focus on the participant's potential"
                                "contribution to the goal and their fit into the interaction schema.",
                            ],
                        ),
                        Section(
                            name="Order of Participants",
                            list=[
                                "The order of participants is important. It should be the order in which they "
                                "should be summoned.",
                                "The first participant will be regarded to as the leader of the group at times, "
                                "so make sure to choose the right one to put first.",
                            ],
                        ),
                        Section(
                            name="Orthogonality of Participants",
                            list=[
                                "Always strive to have participants with orthogonal skills, roles, and specialties. "
                                "That includes personal missions, as well.",
                                "Shared skills and missions is a waste of resources. Aim for maximum coverage of "
                                "skills, roles, specialities and missions.",
                            ],
                        ),
                        Section(
                            name="Composition Suggestion",
                            text="If provided by the user, take into account the "
                            "composition suggestion when deciding how to add/remove.",
                        ),
                    ],
                ),
                Section(
                    name="Updating The Speaker Interaction Schema",
                    list=[
                        "Update the interaction schema to accommodate changes in participants.",
                        "The interaction schema should provide guidelines for a chat manager on how to coordinate the "
                        "participants to achieve the goal. Like an algorithm for choosing the next speaker in the "
                        "conversation.",
                        "The goal of the chat (if provided) must be included in the interaction schema. The whole "
                        "purpose of the interaction schema is to help achieve the goal.",
                        "It should be very clear how the process goes and when it should end.",
                        "The interaction schema should be simple, concise, and very focused on the goal. Formalities "
                        "should be avoided, unless they are necessary for achieving the goal.",
                        "If the chat goal has some output (like an answer), make sure to have the last step be the "
                        "presentation of the final answer by one of the participants as a final message to the chat.",
                    ],
                ),
                Section(
                    name="Updating The Termination Condition",
                    list=[
                        "Update the termination condition to accommodate changes in participants.",
                        "The termination condition should be a simple, concise, and very focused on the goal.",
                        "The chat should terminate when the goal is achieved, or when it is clear that the goal "
                        "cannot be achieved.",
                    ],
                ),
                Section(
                    name="Input",
                    list=[
                        "Goal for the conversation",
                        "Previous messages from the conversation",
                        "Current speaker interaction schema (Optional)",
                        "Current termination condition (Optional)",
                        "Composition suggestion (Optional)",
                        "Available participant tools (Optional)",
                    ],
                ),
                Section(
                    name="Output",
                    text="The output can be compressed, as it will not be used by a human, but by an AI. It should "
                    "include:",
                    list=[
                        "Participants to Remove: List of participants to be removed (if any).",
                        "Participants to Add: List of participants to be added, with their name, role, team (if "
                        "applicable), and personal (or team) mission, and tools (if applicable).",
                        "Updated Interaction Schema: An updated version of the original interaction schema.",
                        "Updated Termination Condition: An updated version of the original termination condition.",
                    ],
                ),
            ]
        )

        return str(system_message)

    def create_compose_chat_participants_first_human_prompt(
        self,
        chat: Chat,
        participant_available_tools: Optional[List[BaseTool]] = None,
        composition_suggestion: Optional[str] = None,
        participants_interaction_schema: Optional[str] = None,
        termination_condition: Optional[str] = None,
    ) -> str:
        messages = chat.get_messages()
        messages_list = [f"- {message.sender_name}: {message.content}" for message in messages]

        available_tools_list = list({f'{x.name}: "{x.description}"' for x in participant_available_tools or []})

        active_participants = chat.get_active_participants()

        prompt = StructuredString(
            sections=[
                Section(name="Chat Goal", text=chat.goal or "No explicit chat goal provided."),
                Section(
                    name="Currently Active Participants", list=[str(participant) for participant in active_participants]
                ),
                Section(
                    name="Current Speaker Interaction Schema",
                    text=participants_interaction_schema or "Not provided. Use your best judgement.",
                ),
                Section(
                    name="Current Termination Condition",
                    text=termination_condition or "Not provided. Use your best judgement.",
                ),
                Section(
                    name="Composition Suggestion",
                    text=composition_suggestion
                    or "Not provided. Use the goal and other inputs to come up with a " "good composition.",
                ),
                Section(
                    name="Available Participant Tools",
                    text="No tools available." if len(available_tools_list) == 0 else None,
                    list=available_tools_list if len(available_tools_list) > 0 else [],
                ),
                Section(
                    name="Chat Messages",
                    text="No messages yet." if len(messages_list) == 0 else None,
                    list=messages_list if len(messages_list) > 0 else [],
                ),
            ]
        )

        return str(prompt)

    def execute_messages(self, messages: Sequence[BaseMessage]) -> str:
        return execute_chat_model_messages(
            messages=messages,
            chat_model=self.chat_model,
            tools=self.generator_tools,
            spinner=self.spinner,
            chat_model_args=self.chat_model_args,
        )
