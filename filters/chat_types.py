from aiogram.filters import Filter
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot, types
from database.orm_query import orm_get_all_admins


class ChatTypeFilter(Filter):

    def __init__(self, chat_types: list[str]) -> None:
        self.chat_types = chat_types

    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type in self.chat_types


class IsAdmin(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: types.Message, bot: Bot, session: AsyncSession) -> bool:
        if await orm_get_all_admins(session, message.from_user.id) is not None:
            return True
        return message.from_user.id in bot.my_admins_list
