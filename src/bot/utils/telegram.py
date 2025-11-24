from aiogram.types import CallbackQuery, Message, User


def require_user(user: User | None) -> User:
    if user is None:
        raise ValueError('User data is not available.')
    return user


def require_message(callback: CallbackQuery) -> Message:
    message = callback.message
    if not isinstance(message, Message):
        raise ValueError('Callback message is not accessible.')
    return message


def require_callback_data(callback: CallbackQuery) -> str:
    payload = callback.data
    if payload is None:
        raise ValueError('Callback data is missing.')
    return payload


def require_text(message: Message) -> str:
    text = message.text
    if text is None:
        raise ValueError('Message text is missing.')
    return text
