import typer
from dotenv import load_dotenv
from halo import Halo

from chatflock.backing_stores import InMemoryChatDataBackingStore
from chatflock.base import Chat
from chatflock.composition_generators.langchain import LangChainBasedAIChatCompositionGenerator
from chatflock.conductors import LangChainBasedAIChatConductor
from chatflock.participants.user import UserChatParticipant
from chatflock.renderers import TerminalChatRenderer
from examples.common import create_chat_model


def automatic_simple_chat_composition(model: str = "gpt-4-1106-preview", temperature: float = 0.0) -> None:
    chat_model = create_chat_model(model=model, temperature=temperature)

    spinner = Halo(spinner="dots")
    user = UserChatParticipant(name="User")
    chat_conductor = LangChainBasedAIChatConductor(
        chat_model=chat_model,
        spinner=spinner,
        # Pass in a composition generator to the conductor
        composition_generator=LangChainBasedAIChatCompositionGenerator(
            chat_model=chat_model,
            spinner=spinner,
        ),
    )
    chat = Chat(
        backing_store=InMemoryChatDataBackingStore(),
        renderer=TerminalChatRenderer(),
        # Set up a proper goal so the composition generator can use it to generate the composition that will best fit
        goal="Come up with a plan for the user to invest their money. The goal is to maximize wealth over the "
        "long-term, while minimizing risk.",
        initial_participants=[user],
    )

    # Not necessary in practice since initiation is done automatically when calling `initiate_chat_with_result`.
    # However, this is needed to eagerly generate the composition. Default is lazy.
    chat_conductor.prepare_chat(chat=chat)

    print(f"Generated Composition:\n=================\n{chat.active_participants_str}\n=================\n\n")

    result = chat_conductor.initiate_dialog(chat=chat)
    print(result)


if __name__ == "__main__":
    load_dotenv()

    typer.run(automatic_simple_chat_composition)
