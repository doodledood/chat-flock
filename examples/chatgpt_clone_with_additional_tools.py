from halo import Halo
from langchain.llms.openai import OpenAI
from langchain.text_splitter import TokenTextSplitter

from chatflock.backing_stores import InMemoryChatDataBackingStore
from chatflock.base import Chat
from chatflock.code.docker import DockerCodeExecutor
from chatflock.code.langchain import CodeExecutionTool
from chatflock.conductors import RoundRobinChatConductor
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv

from chatflock.participants.langchain import LangChainBasedAIChatParticipant
from chatflock.participants.user import UserChatParticipant
from chatflock.renderers import TerminalChatRenderer
from chatflock.web_research import WebSearch
from chatflock.web_research.page_analyzer import OpenAIChatPageQueryAnalyzer
from chatflock.web_research.page_retrievers.selenium_retriever import SeleniumPageRetriever
from chatflock.web_research.search import GoogleSerperSearchResultsProvider
from chatflock.web_research.web_research import WebResearchTool

if __name__ == '__main__':
    load_dotenv()
    chat_model = ChatOpenAI(
        temperature=0.0,
        model='gpt-4-1106-preview'
    )

    chat_model_for_page_analysis = ChatOpenAI(
        temperature=0.0,
        model='gpt-3.5-turbo-1106'
    )

    try:
        max_context_size = OpenAI.modelname_to_contextsize(chat_model_for_page_analysis.model_name)
    except ValueError:
        max_context_size = 12000

    web_search = WebSearch(
        chat_model=chat_model,
        search_results_provider=GoogleSerperSearchResultsProvider(),
        page_query_analyzer=OpenAIChatPageQueryAnalyzer(
            chat_model=chat_model_for_page_analysis,
            # Should `pip install selenium webdriver_manager` to use this
            page_retriever=SeleniumPageRetriever(headless=True),
            text_splitter=TokenTextSplitter(chunk_size=max_context_size, chunk_overlap=max_context_size // 5),
            use_first_split_only=True
        )
    )

    spinner = Halo(spinner='dots')
    ai = LangChainBasedAIChatParticipant(
        name='Assistant',
        chat_model=chat_model,
        tools=[
            CodeExecutionTool(executor=DockerCodeExecutor(spinner=spinner), spinner=spinner),
            WebResearchTool(web_search=web_search, n_results=3, spinner=spinner)
        ],
        spinner=spinner)

    user = UserChatParticipant(name='User')
    participants = [user, ai]

    chat = Chat(
        backing_store=InMemoryChatDataBackingStore(),
        renderer=TerminalChatRenderer(),
        initial_participants=participants
    )

    chat_conductor = RoundRobinChatConductor()
    chat_conductor.initiate_chat_with_result(chat=chat)
