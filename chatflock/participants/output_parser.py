from typing import Generic, Optional, Type

from chatflock.base import ActiveChatParticipant, Chat, TOutputSchema
from chatflock.errors import NoMessagesInChatError
from chatflock.utils import fix_invalid_json, json_string_to_pydantic


class JSONOutputParserChatParticipant(ActiveChatParticipant, Generic[TOutputSchema]):
    def __init__(
        self,
        output_schema: Type[TOutputSchema],
        name: str = "JSON Output Parser",
    ):
        super().__init__(name=name)

        self.output_schema = output_schema
        self.output: Optional[TOutputSchema] = None

    def respond_to_chat(self, chat: Chat) -> str:
        messages = chat.get_messages()
        if len(messages) == 0:
            raise NoMessagesInChatError()

        last_message = messages[-1]

        try:
            json_string = fix_invalid_json(last_message.content, only_cut=True)
            self.output = model = json_string_to_pydantic(json_string, self.output_schema)  # type: ignore

            return f"{model.model_dump_json()} TERMINATE"
        except Exception as e:
            return f"I could not parse the JSON. This was the error: {e}"
