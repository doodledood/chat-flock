class ChatParticipantNotJoinedToChatError(Exception):
    def __init__(self, participant_name: str):
        super().__init__(f'Participant "{participant_name}" is not joined to this chat.')


class ChatParticipantAlreadyJoinedToChatError(Exception):
    def __init__(self, participant_name: str):
        super().__init__(f'Participant "{participant_name}" is already joined to this chat.')


class MessageCouldNotBeParsedError(Exception):
    def __init__(self, message: str):
        super().__init__(f'Message "{message}" could not be parsed.')


class NotEnoughActiveParticipantsInChatError(Exception):
    def __init__(self, n_participants: int = 0):
        super().__init__(f'There are not enough participants in this chat ({n_participants})')


class NoMessagesInChatError(Exception):
    def __init__(self):
        super().__init__('There are no messages in this chat.')


class FunctionNotFoundError(Exception):
    def __init__(self, function_name: str):
        super().__init__(f'Function "{function_name}" not found.')
