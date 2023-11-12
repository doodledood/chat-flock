from halo import Halo

from chatflock.backing_stores import InMemoryChatDataBackingStore
from chatflock.base import Chat
from chatflock.conductors import LangChainBasedAIChatConductor
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv

from chatflock.participants.langchain import LangChainBasedAIChatParticipant
from chatflock.participants.user import UserChatParticipant
from chatflock.renderers import TerminalChatRenderer

if __name__ == '__main__':
    load_dotenv()
    chat_model = ChatOpenAI(
        temperature=0.0,
        model='gpt-4-1106-preview'
    )

    spinner = Halo(spinner='dots')
    ai = LangChainBasedAIChatParticipant(name='Assistant',
                                         role='Boring Serious AI Assistant',
                                         chat_model=chat_model,
                                         spinner=spinner)
    rob = LangChainBasedAIChatParticipant(name='Rob', role='Funny Prankster',
                                          personal_mission='Take the lead and try to prank the boring AI. Collaborate '
                                                           'with the user when relevant and make him laugh!',
                                          chat_model=chat_model,
                                          spinner=spinner)
    user = UserChatParticipant(name='User')
    participants = [user, ai, rob]

    chat = Chat(
        backing_store=InMemoryChatDataBackingStore(),
        renderer=TerminalChatRenderer(),
        initial_participants=participants,
        goal='Make the user laugh by pranking the boring AI.',
    )

    chat_conductor = LangChainBasedAIChatConductor(
        chat_model=chat_model,
        spinner=spinner,
        participants_interaction_schema=
        f'Assistant should go first. Then, rob should jump in and  take the lead and go back and forth with the '
        f'assistant trying to prank him. Once a prank is done by Rob the user come in and give feedback or collaborate '
        f'with Rob. However the majority of the prank should be done by Rob.',
        termination_condition='One laugh is enough. Terminate the chat when the user finds a prank funny.'
    )

    chat_conductor.initiate_chat_with_result(chat=chat)
