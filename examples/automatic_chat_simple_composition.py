from dotenv import load_dotenv
from halo import Halo
from langchain.cache import SQLiteCache
from langchain.chat_models import ChatOpenAI
from langchain.globals import set_llm_cache

from chatflock.backing_stores import InMemoryChatDataBackingStore
from chatflock.base import Chat
from chatflock.composition_generators.langchain import LangChainBasedAIChatCompositionGenerator
from chatflock.conductors import LangChainBasedAIChatConductor
from chatflock.participants.user import UserChatParticipant
from chatflock.renderers import TerminalChatRenderer

if __name__ == "__main__":
    load_dotenv()

    set_llm_cache(SQLiteCache(database_path="../../output/llm_cache.db"))

    chat_model = ChatOpenAI(temperature=0.0, model="gpt-4-1106-preview")

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
    chat_conductor.initialize_chat(chat=chat)

    print(f"Generated Composition:\n=================\n{chat.active_participants_str}\n=================\n\n")

    result = chat_conductor.initiate_chat_with_result(chat=chat)
    print(result)
