from dotenv import load_dotenv
from halo import Halo

from chatflock.backing_stores import InMemoryChatDataBackingStore
from chatflock.base import Chat
from chatflock.composition_generators.langchain import LangChainBasedAIChatCompositionGenerator
from chatflock.conductors import LangChainBasedAIChatConductor
from chatflock.participants.internal_group import InternalGroupBasedChatParticipant
from chatflock.participants.user import UserChatParticipant
from chatflock.renderers import TerminalChatRenderer
from examples.common import create_chat_model


def automatic_internal_group_participant(model: str = "gpt-4-1106-preview", temperature: float = 0.0) -> None:
    chat_model = create_chat_model(model=model, temperature=temperature)

    spinner = Halo(spinner="dots")
    comedy_team = InternalGroupBasedChatParticipant(
        group_name="Financial Team",
        mission="Ensure the user's financial strategy maximizes wealth over the long term without too much risk.",
        chat=Chat(backing_store=InMemoryChatDataBackingStore(), renderer=TerminalChatRenderer()),
        chat_conductor=LangChainBasedAIChatConductor(
            chat_model=chat_model,
            spinner=spinner,
            composition_generator=LangChainBasedAIChatCompositionGenerator(chat_model=chat_model, spinner=spinner),
        ),
        spinner=spinner,
    )
    user = UserChatParticipant(name="User")
    participants = [user, comedy_team]

    chat = Chat(
        backing_store=InMemoryChatDataBackingStore(), renderer=TerminalChatRenderer(), initial_participants=participants
    )

    chat_conductor = LangChainBasedAIChatConductor(
        participants_interaction_schema="The user should take the lead and go back and forth with the financial team,"
        " collaborating on the financial strategy. The user should be the one to "
        "initiate the chat.",
        chat_model=chat_model,
        spinner=spinner,
    )

    # Not necessary in practice since initiation is done automatically when calling `initiate_chat_with_result`.
    # However, this is needed to eagerly generate the composition. Default is lazy.
    chat_conductor.prepare_chat(chat=chat)
    print(f"\nGenerated composition:\n=================\n{chat.active_participants_str}\n=================\n\n")

    # You can also pass in a composition suggestion here.
    result = chat_conductor.initiate_dialog(chat=chat)
    print(result)


if __name__ == "__main__":
    load_dotenv()
