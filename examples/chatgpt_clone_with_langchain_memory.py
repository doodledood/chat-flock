from dotenv import load_dotenv
from halo import Halo
from langchain.chat_models import ChatOpenAI
from langchain.llms.openai import OpenAI
from langchain.memory import ConversationSummaryBufferMemory

from chatflock.backing_stores import InMemoryChatDataBackingStore
from chatflock.backing_stores.langchain import LangChainMemoryBasedChatDataBackingStore
from chatflock.base import Chat, ChatDataBackingStore
from chatflock.conductors import RoundRobinChatConductor
from chatflock.participants.langchain import LangChainBasedAIChatParticipant
from chatflock.participants.user import UserChatParticipant
from chatflock.renderers import TerminalChatRenderer

if __name__ == "__main__":
    load_dotenv()
    chat_model = ChatOpenAI(temperature=0.0, model="gpt-4-1106-preview")

    spinner = Halo(spinner="dots")
    ai = LangChainBasedAIChatParticipant(name="Assistant", chat_model=chat_model, spinner=spinner)
    user = UserChatParticipant(name="User")
    participants = [user, ai]

    try:
        memory = ConversationSummaryBufferMemory(
            llm=chat_model, max_token_limit=OpenAI.modelname_to_contextsize(chat_model.model_name)
        )
        backing_store: ChatDataBackingStore = LangChainMemoryBasedChatDataBackingStore(memory=memory)
    except ValueError:
        backing_store = InMemoryChatDataBackingStore()

    chat = Chat(backing_store=backing_store, renderer=TerminalChatRenderer(), initial_participants=participants)

    chat_conductor = RoundRobinChatConductor()
    chat_conductor.initiate_chat_with_result(chat=chat)
