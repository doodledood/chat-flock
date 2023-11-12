from datetime import datetime
from typing import Dict, Any, List, Optional

from halo import Halo
from langchain.chat_models.base import BaseChatModel
from langchain.schema import BaseMessage, AIMessage, HumanMessage, SystemMessage, BaseRetriever, Document
from langchain.tools import BaseTool

from chatflock.ai_utils import execute_chat_model_messages
from chatflock.base import ChatMessage, Chat, ActiveChatParticipant
from chatflock.structured_string import Section, StructuredString


class LangChainBasedAIChatParticipant(ActiveChatParticipant):
    personal_mission: str
    role: str
    chat_model: BaseChatModel
    chat_model_args: Dict[str, Any]
    other_prompt_sections: List[Section]
    retriever: Optional[BaseRetriever] = None
    tools: Optional[List[BaseTool]] = None,
    ignore_group_chat_environment: bool = False
    spinner: Optional[Halo] = None
    include_timestamp_in_messages: bool = False

    class Config:
        arbitrary_types_allowed = True

    def __init__(self,
                 name: str,
                 chat_model: BaseChatModel,
                 symbol: str = '🤖',
                 role: str = 'AI Assistant',
                 personal_mission: str = 'Be a helpful AI assistant.',
                 other_prompt_sections: Optional[List[Section]] = None,
                 retriever: Optional[BaseRetriever] = None,
                 tools: Optional[List[BaseTool]] = None,
                 chat_model_args: Optional[Dict[str, Any]] = None,
                 spinner: Optional[Halo] = None,
                 ignore_group_chat_environment: bool = False,
                 include_timestamp_in_messages: bool = False,
                 **kwargs
                 ):
        super().__init__(name=name, symbol=symbol, **kwargs)

        self.role = role
        self.chat_model = chat_model
        self.chat_model_args = chat_model_args or {}
        self.other_prompt_sections = other_prompt_sections or []
        self.ignore_group_chat_environment = ignore_group_chat_environment
        self.include_timestamp_in_messages = include_timestamp_in_messages
        self.retriever = retriever
        self.tools = tools
        self.spinner = spinner
        self.personal_mission = personal_mission

    def create_system_message(self, chat: 'Chat', relevant_docs: List[Document]):
        now = datetime.now()
        pretty_datetime = now.strftime('%m-%d-%Y %H:%M:%S')

        base_sections = [
            Section(name='Current Time', text=pretty_datetime),
            Section(name='Name', text=self.name),
            Section(name='Role', text=self.role),
            Section(name='Personal Mission', text=self.personal_mission),
            Section(name='Additional Context for Response',
                    text='None' if len(
                        relevant_docs) == 0 else 'The following documents may be relevant for your response, only use '
                                                 'them for context for a better response, if applicable',
                    sub_sections=[
                        Section(name=f'Document {i + 1}', text=f'```{doc.page_content}```') for i, doc in
                        enumerate(relevant_docs)
                    ]),
            Section(name='Response Message Format', list=[
                'Your response should be the message you want to send to the group chat as your own name, '
                'role, and personal mission.',
                'Must not include any prefix (e.g., timestamp, sender name, etc.).',
                'Response must be a message as will be shown in the chat (timestamp and sender name are '
                'system-generated for you).'
            ], sub_sections=[
                Section(name='Well-Formatted Chat Response Examples', list=[
                    '"Hello, how are you?"'
                ]),
                Section(name='Badly-Formatted Chat Response Examples', list=[
                    ('"[TIMESTAMP] John: Hello, how are you?"' if self.include_timestamp_in_messages else
                     '"John: Hello, how are you?"'),
                ])
            ])
        ]

        active_participants = chat.get_active_participants()
        if self.ignore_group_chat_environment:
            system_message = StructuredString(sections=[
                *base_sections,
                *self.other_prompt_sections
            ])
        else:
            system_message = StructuredString(
                sections=[
                    *base_sections,
                    Section(name='Chat', sub_sections=[
                        Section(name='Name', text=chat.name or 'No name provided. Just a general chat.'),
                        Section(name='Goal', text=chat.goal or 'No explicit chat goal provided.'),
                        Section(name='Participants', text='\n'.join(
                            [f'- {str(p)}{" -> This is you." if p.name == self.name else ""}' \
                             for p in active_participants])),
                        Section(name='Rules', list=[
                            'You do not have to respond directly to the one who sent you a message. You can respond '
                            'to anyone in the group chat.',
                            'You cannot have private conversations with other participants. Everyone can see all '
                            'messages sent by all other participants.',
                        ]),
                        Section(name='Previous Chat Messages', list=[
                            'Messages are prefixed by a timestamp and the sender\'s name (could also be everyone). ',
                            'The prefix is for context only; it\'s not actually part of the message they sent. ',
                            ('Example: "[TIMESTAMP] John: Hello, how are you?"' if self.include_timestamp_in_messages
                             else 'Example: "John: Hello, how are you?"'),
                            'Some messages could have been sent by participants who are no longer a part of this '
                            'conversation. Use their contents for context only; do not talk to them.',
                            'In your response only include the message without the prefix.'
                        ])
                    ]),
                    *self.other_prompt_sections,
                ]
            )

        return str(system_message)

    def chat_messages_to_chat_model_messages(self, chat_messages: List[ChatMessage]) -> \
            List[BaseMessage]:
        messages = []
        for message in chat_messages:
            if self.include_timestamp_in_messages:
                pretty_datetime = message.timestamp.strftime('%m-%d-%Y %H:%M:%S')
                content = f'[{pretty_datetime}] '
            else:
                content = ''

            if self.ignore_group_chat_environment:
                content += f'{message.sender_name}: {message.content}'
            else:
                content += message.content

            if message.sender_name == self.name:
                messages.append(AIMessage(content=content))
            else:
                messages.append(HumanMessage(content=content))

        if len(messages) == 0:
            messages.append(HumanMessage(content=f'SYSTEM: The chat has started.'))

        return messages

    def respond_to_chat(self, chat: Chat) -> str:
        if self.spinner is not None:
            self.spinner.start(text=f'{str(self)} is thinking...')

        chat_messages = chat.get_messages()

        if self.retriever is not None and len(chat_messages) > 0:
            relevant_docs = self.get_relevant_docs(messages=chat_messages)
        else:
            relevant_docs = []

        system_message = self.create_system_message(chat=chat, relevant_docs=relevant_docs)

        all_messages = self.chat_messages_to_chat_model_messages(chat_messages)
        all_messages = [
            SystemMessage(content=system_message),
            *all_messages
        ]

        message_content = self.execute_messages(messages=all_messages)

        if self.spinner is not None:
            self.spinner.stop()

        potential_prefix = f'{self.name}:'
        if message_content.startswith(potential_prefix):
            message_content = message_content[len(potential_prefix):].strip()

        return message_content

    def get_relevant_docs(self, messages: List[ChatMessage]) -> List[Document]:
        return self.retriever.get_relevant_documents(query=messages[-1].content)

    def execute_messages(self, messages: List[BaseMessage]) -> str:
        return execute_chat_model_messages(
            messages=messages,
            chat_model=self.chat_model,
            tools=self.tools,
            spinner=self.spinner,
            chat_model_args=self.chat_model_args
        )

    def __str__(self):
        return f'{self.symbol} {self.name} ({self.role})'

    def detailed_str(self, level: int = 0):
        prefix = '    ' * level

        tool_names = ', '.join([tool.name for tool in self.tools or []])
        if tool_names == '':
            tool_names = 'None'

        return (f'{prefix}- Name: {self.name}\n{prefix}  Role: {self.role}\n{prefix}  Symbol: {self.symbol}\n'
                f'{prefix}  Personal Mission: "{self.personal_mission}"\n{prefix}  Tools: {tool_names}')
