from halo import Halo
from langchain.cache import SQLiteCache
from langchain.globals import set_llm_cache

from chatflock.backing_stores import InMemoryChatDataBackingStore
from chatflock.base import Chat
from chatflock.composition_generators.langchain import LangChainBasedAIChatCompositionGenerator
from chatflock.conductors import LangChainBasedAIChatConductor, RoundRobinChatConductor
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv

from chatflock.participants.internal_group import InternalGroupBasedChatParticipant
from chatflock.participants.user import UserChatParticipant
from chatflock.renderers import TerminalChatRenderer

if __name__ == '__main__':
    load_dotenv()

    set_llm_cache(SQLiteCache(database_path='../../output/llm_cache.db'))

    chat_model = ChatOpenAI(
        temperature=0.0,
        model='gpt-4-1106-preview'
    )

    spinner = Halo(spinner='dots')
    comedy_team = InternalGroupBasedChatParticipant(
        group_name='Financial Team',
        mission='Ensure the user\'s financial strategy maximizes wealth over the long term without too much risk.',
        chat=Chat(
            backing_store=InMemoryChatDataBackingStore(),
            renderer=TerminalChatRenderer()
        ),
        chat_conductor=LangChainBasedAIChatConductor(
            chat_model=chat_model,
            spinner=spinner,
            composition_generator=LangChainBasedAIChatCompositionGenerator(
                chat_model=chat_model,
                spinner=spinner
            )
        ),
        spinner=spinner
    )
    user = UserChatParticipant(name='User')
    participants = [user, comedy_team]

    chat = Chat(
        backing_store=InMemoryChatDataBackingStore(),
        renderer=TerminalChatRenderer(),
        initial_participants=participants
    )

    chat_conductor = LangChainBasedAIChatConductor(
        participants_interaction_schema='The user should take the lead and go back and forth with the financial team,'
                                        ' collaborating on the financial strategy. The user should be the one to '
                                        'initiate the chat.',
        chat_model=chat_model,
        spinner=spinner
    )

    # Not necessary in practice since initiation is done automatically when calling `initiate_chat_with_result`.
    # However, this is needed to eagerly generate the composition. Default is lazy.
    chat_conductor.initialize_chat(
        chat=chat)
    print(f'\nGenerated composition:\n=================\n{chat.active_participants_str}\n=================\n\n')

    # You can also pass in a composition suggestion here.
    result = chat_conductor.initiate_chat_with_result(chat=chat)
    print(result)

