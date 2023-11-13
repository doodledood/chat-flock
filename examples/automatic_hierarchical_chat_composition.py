from typing import Any

import typer
from dotenv import load_dotenv
from halo import Halo
from langchain.memory import ConversationSummaryBufferMemory

from chatflock.backing_stores import InMemoryChatDataBackingStore
from chatflock.backing_stores.langchain import LangChainMemoryBasedChatDataBackingStore
from chatflock.base import Chat, ChatDataBackingStore
from chatflock.code.langchain import CodeExecutionTool
from chatflock.code.local import LocalCodeExecutor
from chatflock.composition_generators.langchain import LangChainBasedAIChatCompositionGenerator
from chatflock.conductors import LangChainBasedAIChatConductor
from chatflock.participants.user import UserChatParticipant
from chatflock.renderers import TerminalChatRenderer
from examples.common import create_chat_model, get_max_context_size


def automatic_hierarchical_chat_composition(model: str = "gpt-4-1106-preview", temperature: float = 0.0) -> None:
    chat_model = create_chat_model(model=model, temperature=temperature)

    def create_default_backing_store() -> ChatDataBackingStore:
        max_context_size = get_max_context_size(chat_model)
        if max_context_size is not None:
            return LangChainMemoryBasedChatDataBackingStore(
                memory=ConversationSummaryBufferMemory(llm=chat_model, max_token_limit=max_context_size)
            )
        else:
            return InMemoryChatDataBackingStore()

    def create_chat(**kwargs: Any) -> Chat:
        return Chat(backing_store=create_default_backing_store(), renderer=TerminalChatRenderer(), **kwargs)

    spinner = Halo(spinner="dots")
    user = UserChatParticipant(name="User")
    chat_conductor = LangChainBasedAIChatConductor(
        chat_model=chat_model,
        spinner=spinner,
        # Pass in a composition generator to the conductor
        composition_generator=LangChainBasedAIChatCompositionGenerator(
            chat_model=chat_model,
            spinner=spinner,
            generate_composition_extra_args=dict(create_internal_chat=create_chat),
            participant_available_tools=[CodeExecutionTool(executor=LocalCodeExecutor(), spinner=spinner)],
        ),
    )
    chat = create_chat(
        # Set up a proper goal so the composition generator can use it to generate the composition that will best fit
        goal="The goal is to create the best website for the user.",
        initial_participants=[user],
    )

    # It's not necessary in practice to manually call `initialize_chat` since initiation is done automatically
    # when calling `initiate_chat_with_result`. However, this is needed to eagerly generate the composition.
    # Default is lazy and will happen when the chat is initiated.
    chat_conductor.initialize_chat(
        chat=chat,
        # Only relevant when passing in a composition generator
        composition_suggestion="DevCompany: Includes a CEO, Product Team, Marketing Team, and a Development "
        "Department. The Development Department includes a Director, QA Team and Development "
        "Team.",
    )
    print(f"\nGenerated composition:\n=================\n{chat.active_participants_str}\n=================\n\n")

    # You can also pass in a composition suggestion here.
    result = chat_conductor.initiate_chat_with_result(chat=chat)
    print(result)


if __name__ == "__main__":
    load_dotenv()

    typer.run(automatic_hierarchical_chat_composition)
