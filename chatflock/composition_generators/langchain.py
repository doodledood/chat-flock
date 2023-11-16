from typing import Any, Dict, List, Optional, Sequence

from halo import Halo
from langchain.chat_models.base import BaseChatModel
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain.tools import BaseTool

from chatflock.ai_utils import execute_chat_model_messages
from chatflock.base import ActiveChatParticipant, Chat, ChatCompositionGenerator, GeneratedChatComposition
from chatflock.composition_generators import CreateTeamCompositionForGoalOutputSchema
from chatflock.parsing_utils import string_output_to_pydantic
from chatflock.participants.langchain import LangChainBasedAIChatParticipant
from chatflock.structured_string import Section, StructuredString


class LangChainBasedAIChatCompositionGenerator(ChatCompositionGenerator):
    def __init__(
        self,
        chat_model: BaseChatModel,
        fixed_team_members: Optional[List[ActiveChatParticipant]] = None,
        generator_tools: Optional[List[BaseTool]] = None,
        participant_available_tools: Optional[List[BaseTool]] = None,
        chat_model_args: Optional[Dict[str, Any]] = None,
        spinner: Optional[Halo] = None,
        n_output_parsing_tries: int = 3,
        generate_composition_extra_args: Optional[Dict[str, Any]] = None,
    ):
        self.chat_model = chat_model
        self.chat_model_args = chat_model_args or {}
        self.fixed_team_members = fixed_team_members or []
        self.generator_tools = generator_tools
        self.participant_available_tools = participant_available_tools
        self.spinner = spinner
        self.n_output_parsing_tries = n_output_parsing_tries
        self.generate_composition_extra_args = generate_composition_extra_args or {}

        self.participant_tool_names_to_tools = {tool.name: tool for tool in self.participant_available_tools or []}

    def generate_composition_for_chat(
        self,
        chat: Chat,
        goal: str,
        composition_suggestion: Optional[str] = None,
        interaction_schema: Optional[str] = None,
    ) -> GeneratedChatComposition:
        if composition_suggestion is None:
            composition_suggestion = self.generate_composition_extra_args.get("composition_suggestion", None)

        if interaction_schema is None:
            interaction_schema = self.generate_composition_extra_args.get("participants_interaction_schema", None)

        if self.spinner is not None:
            self.spinner.start(text="The Chat Composition Generator is creating a team composition for the goal...")

        # Ask the AI to select the next speaker.
        messages = [
            SystemMessage(content=self.create_compose_team_system_prompt()),
            HumanMessage(
                content=self.create_compose_team_first_human_prompt(
                    goal=goal,
                    participant_available_tools=self.participant_available_tools,
                    composition_suggestion=composition_suggestion,
                    participants_interaction_schema=interaction_schema,
                )
            ),
        ]

        result = self.execute_messages(messages=messages)

        output = string_output_to_pydantic(
            output=result,
            chat_model=self.chat_model,
            output_schema=CreateTeamCompositionForGoalOutputSchema,
            n_tries=self.n_output_parsing_tries,
            spinner=self.spinner,
            hide_message=False,
        )

        participants_to_add_names = [str(participant) for participant in output.team_composition]

        if self.spinner is not None:
            name = "The Chat Composition Generator"
            if chat.name is not None:
                name = f"{name} ({chat.name})"

            if len(output.team_composition) == 0:
                self.spinner.succeed(text=f"{name} has decided the existing team composition is satisfactory.")
            else:
                self.spinner.succeed(
                    text=f"{name} has decided to add the following participants: "
                    f'{", ".join(participants_to_add_names)}'
                )

        participants: Dict[str, ActiveChatParticipant] = {p.name: p for p in self.fixed_team_members}

        for participant in output.team_composition:
            if participant.name in participants:
                continue

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
                other_prompt_sections=[
                    Section(
                        name="Chat Main Goal",
                        text=goal or "No explicit goal provided.",
                    ),
                    Section(
                        name="Chat Participant Interaction Schema",
                        text=interaction_schema or "Not provided. Use your best judgement.",
                    ),
                ],
            )

            participants[chat_participant.name] = chat_participant

        return GeneratedChatComposition(
            participants=list(participants.values()),
            participants_interaction_schema=output.interaction_schema,
        )

    def create_compose_team_system_prompt(self) -> str:
        system_message = StructuredString(
            sections=[
                Section(
                    name="Mission",
                    text="Create a team capable of accomplishing objectives through effective communication and the "
                    "use of tools, focusing on the essential elements of the objectives.",
                ),
                Section(
                    name="Goal Simplification",
                    list=[
                        "Distill the main objective into clear, simple, and actionable components.",
                        "Ensure each component is addressable via verbal or tool-based actions.",
                    ],
                    list_item_prefix=None,
                ),
                Section(
                    name="Team Assembly",
                    sub_sections=[
                        Section(
                            name="Team Selection",
                            list=[
                                "Select individuals with the necessary conversational abilities and tool proficiency.",
                                "Allocate roles and tasks that correspond to the objective's components.",
                                "Invent role-based monikers for team members.",
                                "Include all the fixed team members in the new team; take fixed team members into "
                                "account when allocating roles and tasks. For example: If a User is in the fixed team, "
                                "and the goal is about helping the user out somehow, make sure the User is a part of "
                                "the new team.",
                                "Ambiguity of roles should be avoided. For example: If a User is in the fixed team, "
                                "do not assign a new member the role of a User or Client.",
                            ],
                        ),
                        Section(
                            name="Skill Diversity",
                            list=["Assemble a skill set that spans all aspects of the objective."],
                        ),
                    ],
                ),
                Section(
                    name="Team Interaction Schema",
                    list=[
                        "Design a blueprint for team interactions, dialog flow, and tool application for each "
                        "component of the objective.",
                        "Incorporate stages, interaction patterns, failure cases, contingency plans, "
                        "and success metrics.",
                        "Fixed members must be included in the interaction outline. For example: If a User is in the "
                        "fixed team, and the goal is about helping the user out somehow, make sure the User is an "
                        "integral part of the interaction schema.",
                        "The interaction schema should be granular and detailed, including the phases, how members "
                        "should interact with each other to achieve the goal including: failure cases, "
                        "stoppage criteria, success metrics, interaction patterns and details on team member "
                        "interactions including exactly who should talk to who, when, tool usage, etc.",
                        "Generally, everything that a manager of the team should know about to direct the team toward "
                        "goal completion.",
                    ],
                ),
                Section(
                    name="Tool Distribution",
                    list=["Match tools from the provided inventory to team members to facilitate their tasks."],
                ),
                Section(
                    name="Input Requirements",
                    list=[
                        "Required: Objective or task description.",
                        "Optional: Proposals for interaction outline, team structure, and tool inventory.",
                    ],
                ),
                Section(
                    name="Output Details",
                    list=[
                        "Recommend a team with designated roles, tasks, and tools.",
                        "Provide an interaction outline to guide the achievement of the objective.",
                    ],
                ),
                Section(
                    name="Output Structure",
                    sub_sections=[
                        Section(
                            name="Objective Breakdown",
                            text="Itemize the main objective into practical tasks for communication and tool use.",
                        ),
                        Section(
                            name="Team Roster",
                            text="Enumerate team members with identifiers, roles, missions, and tools. "
                            "Format: - emojii (role): mission (tools)",
                        ),
                        Section(
                            name="Team Interaction Schema",
                            text="Present a detailed, structured schema for team interactions based on "
                            "the TEAM INTERACTION SCHEMA instructions.",
                        ),
                    ],
                ),
            ]
        )

        return str(system_message)

    def create_compose_team_first_human_prompt(
        self,
        goal: str,
        participant_available_tools: Optional[List[BaseTool]] = None,
        composition_suggestion: Optional[str] = None,
        participants_interaction_schema: Optional[str] = None,
    ) -> str:
        available_tools_list = list({f'{x.name}: "{x.description}"' for x in participant_available_tools or []})

        prompt = StructuredString(
            sections=[
                Section(name="Goal", text=goal or "No explicit goal provided."),
                Section(
                    name="Suggested Interaction Schema",
                    text=participants_interaction_schema or "Not provided. Use your best judgement.",
                ),
                Section(
                    name="Suggested Composition",
                    text=composition_suggestion
                    or "Not provided. Use the goal and other inputs to come up with a good composition.",
                ),
                Section(
                    name="Fixed Team Members",
                    list=[f"{participant.detailed_str()}" for participant in self.fixed_team_members],
                ),
                Section(
                    name="Tool Inventory",
                    text="No tools available." if len(available_tools_list) == 0 else None,
                    list=available_tools_list if len(available_tools_list) > 0 else [],
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
