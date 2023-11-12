from dotenv import load_dotenv
from halo import Halo
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores.chroma import Chroma

from chatflock.backing_stores import InMemoryChatDataBackingStore
from chatflock.base import Chat
from chatflock.conductors import RoundRobinChatConductor
from chatflock.participants.langchain import LangChainBasedAIChatParticipant
from chatflock.participants.user import UserChatParticipant
from chatflock.renderers import TerminalChatRenderer

if __name__ == "__main__":
    load_dotenv()
    chat_model = ChatOpenAI(temperature=0.0, model="gpt-4-1106-preview")

    spinner = Halo(spinner="dots")

    # Set up a simple document store.
    texts = ["The user's name is Eric.", "The user likes to eat Chocolate."]

    # Make sure you have OPENAI_API_KEY set in your environment variables.
    embeddings = OpenAIEmbeddings()

    # Make sure you install chromadb: `pip install chromadb`
    db = Chroma.from_texts(texts, embeddings)
    retriever = db.as_retriever()

    ai = LangChainBasedAIChatParticipant(
        name="Assistant",
        chat_model=chat_model,
        # Pass the retriever to the AI participant
        retriever=retriever,
        spinner=spinner,
    )
    user = UserChatParticipant(name="User")
    participants = [user, ai]

    chat = Chat(
        backing_store=InMemoryChatDataBackingStore(), renderer=TerminalChatRenderer(), initial_participants=participants
    )

    chat_conductor = RoundRobinChatConductor()
    chat_conductor.initiate_chat_with_result(chat=chat)
