# Quickstart

## Installation

ChatFlock is available on [PyPI](https://pypi.org/project/chat-flock/) and can be installed using pip or poetry:

### Pip

```bash
pip install chat-flock
```

### Poetry

```bash
poetry add chat-flock
```

## Simple Usage

### ChatGPT Clone

```python
from halo import Halo
from langchain.chat_models import ChatOpenAI
from chatflock.backing_stores.in_memory import InMemoryChatDataBackingStore
from chatflock.base import Chat
from chatflock.conductors.round_robin import RoundRobinChatConductor
from chatflock.participants.langchain import LangChainBasedAIChatParticipant
from chatflock.participants.user import UserChatParticipant
from chatflock.renderers.terminal import TerminalChatRenderer

chat_model = ChatOpenAI(temperature=0.0, model='gpt-4-1106-preview')

spinner = Halo(spinner="dots")
ai = LangChainBasedAIChatParticipant(name="Assistant", chat_model=chat_model, spinner=spinner)
user = UserChatParticipant(name="User")
participants = [user, ai]

chat = Chat(
    backing_store=InMemoryChatDataBackingStore(), renderer=TerminalChatRenderer(), initial_participants=participants
)

chat_conductor = RoundRobinChatConductor()
chat_conductor.initiate_dialog(chat=chat)
