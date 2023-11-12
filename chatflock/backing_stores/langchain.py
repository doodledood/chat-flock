import datetime
import re
from typing import List, Optional, Callable

from langchain.memory.chat_memory import BaseChatMemory
from langchain.schema import BaseMessage

from chatflock.backing_stores.in_memory import InMemoryChatDataBackingStore
from chatflock.base import ChatMessage, ChatParticipant


def base_message_to_chat_message(base_message: BaseMessage) -> ChatMessage:
    content = str(base_message.content)

    pattern = re.compile(r'(\d+)\.\s*(.+?):\s*(.*)', re.DOTALL)
    match = pattern.match(content)

    if not match:
        return ChatMessage(
            id=-1,
            sender_name='SYSTEM',
            content=content
        )

    id_number = int(match.group(1))
    sender_name = match.group(2)
    message_content = match.group(3)

    return ChatMessage(
        id=id_number,
        sender_name=sender_name,
        content=message_content
    )


class LangChainMemoryBasedChatDataBackingStore(InMemoryChatDataBackingStore):
    no_output_message: str = '##NO_OUTPUT##'

    def __init__(self,
                 memory: BaseChatMemory,
                 memory_key_getter: Optional[Callable[[BaseChatMemory], str]] = None,
                 messages: Optional[List[ChatMessage]] = None,
                 include_timestamp_in_messages: bool = False,
                 participants: Optional[List[ChatParticipant]] = None):
        super().__init__(participants=participants)

        self.memory = memory
        self.include_timestamp_in_messages = include_timestamp_in_messages

        if memory_key_getter is None:
            def default_memory_key_getter(memory: BaseChatMemory) -> str:
                if hasattr(memory, 'memory_key'):
                    return str(memory.memory_key)

                return self.memory.output_key or 'history'

            self.memory_key_getter: Callable[[BaseChatMemory], str] = default_memory_key_getter
        else:
            self.memory_key_getter = memory_key_getter

    def get_messages(self) -> List[ChatMessage]:
        prev_return_messages = self.memory.return_messages

        self.memory.return_messages = True

        memory_key = self.memory_key_getter(self.memory)
        base_messages = self.memory.load_memory_variables({})[memory_key]
        chat_messages = [base_message_to_chat_message(base_message) for base_message in base_messages if
                         base_message.content != self.no_output_message]

        self.memory.return_messages = prev_return_messages

        return chat_messages

    def add_message(self, sender_name: str, content: str, timestamp: Optional[datetime.datetime] = None) -> ChatMessage:
        message = super().add_message(sender_name=sender_name, content=content)

        prefix = ''
        if self.include_timestamp_in_messages:
            pretty_datetime = message.timestamp.strftime('%m-%d-%Y %H:%M:%S')
            prefix = f'[{pretty_datetime}] '

        self.memory.save_context({
            "input": f'{prefix}{message.id}. {message.sender_name}: {message.content}'
        }, {
            'output': self.no_output_message
        })

        return message

    def clear_messages(self):
        super().clear_messages()

        self.memory.clear()
