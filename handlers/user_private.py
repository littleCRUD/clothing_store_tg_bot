import calendar
from datetime import datetime
from aiogram import F, types, Router, Bot
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.ext.asyncio import AsyncSession
from database.orm_query import orm_add_to_basket, orm_add_user, orm_delete_from_basket
from filters.chat_types import ChatTypeFilter
from handlers.menu_subpocces import get_menu_content
from kbds.inline import MenuCallBack, get_callback_btns


user_private_router = Router()
user_private_router.message.filter(ChatTypeFilter(["private"]))


# Ловим команду старт и отвечаем основным меню
@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message, session: AsyncSession):
    media, reply_murkup = await get_menu_content(session, level=0, menu_name="main")
    await message.answer_photo(
        media.media, caption=media.caption, reply_markup=reply_murkup
    )


# Добавить товар в корзину
async def add_to_basket(
    callback: types.CallbackQuery,
    callback_data: MenuCallBack,
    session: AsyncSession,
):
    user = callback.from_user
    await orm_add_user(
        session=session,
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=None,
    )
    await orm_add_to_basket(
        session=session, user_id=user.id, product_id=callback_data.product_id
    )
    await callback.answer("Товар добавлен в корзину")


class RegDeliver(StatesGroup):
    """Класс для отслеживания стостоянии данных о даставке"""

    num = State()
    addr = State()
    month = State()
    day = State()
    time = State()


# Ловим меню callback
@user_private_router.callback_query(MenuCallBack.filter())
async def user_menu(
    callback: types.CallbackQuery,
    callback_data: MenuCallBack,
    session: AsyncSession,
    state: FSMContext | None = None,
):

    if callback_data.menu_name == "add_to_basket":
        await add_to_basket(callback, callback_data, session)
        return
    if callback_data.menu_name == "reg_deliver":
        await state.update_data(
            callback={
                "message_id": callback.message.message_id,
                "chat_id": callback.message.chat.id,
            }
        )

        await callback.message.delete()
        await callback.message.answer(
            "Введите номер телефона\nВ формате +7 999 999 99 99"
        )
        await callback.answer()
        await state.set_state(RegDeliver.num)
        return

    media, reply_markup = await get_menu_content(
        session=session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        category=callback_data.category,
        page=callback_data.page,
        product_id=callback_data.product_id,
        user_id=callback.from_user.id,
    )

    await callback.message.edit_media(media=media, reply_markup=reply_markup)
    await callback.answer()


# Ловим состояние num (номер телефона юзера), встаем в состояние addr (ввод адреса)
@user_private_router.message(StateFilter(RegDeliver.num), F.text)
async def get_user_num(message: types.Message, state: FSMContext, bot: Bot):
    await state.update_data(num=message.text)
    await state.update_data(user_id=message.from_user.id)
    await message.delete()
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    await state.set_state(RegDeliver.addr)
    await message.answer("Введите адрес доставки\nВ формате: улица, дом, квартира")


# Ловим состояние addr, встаем в состояние месяц
@user_private_router.message(StateFilter(RegDeliver.addr), F.text)
async def get_user_addr(message: types.Message, state: FSMContext, bot: Bot):
    await state.update_data(addr=message.text)
    await message.delete()
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    kbds = {
        f"  {abr}  ": f"{num}"
        for num, abr in enumerate(calendar.month_abbr)
        if abr and num
    }
    await message.answer(
        "Выберите месяц", reply_markup=get_callback_btns(btns=kbds, sizes=(4,))
    )
    await state.set_state(RegDeliver.month)


# Ловим состояние month, встаем в состояние day
@user_private_router.callback_query(StateFilter(RegDeliver.month))
async def get_user_month(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(month=callback.data)
    days = (calendar.monthrange(datetime.now().date().year, int(callback.data)))[-1]
    kbds = {f"   {day}   ": f"{day}" for day in range(1, days + 1)}
    await callback.message.delete()
    await callback.message.answer(
        "Выберите день", reply_markup=get_callback_btns(btns=kbds, sizes=(6,))
    )
    await callback.answer()
    await state.set_state(RegDeliver.day)


# Ловим состояние day, встаем в состояние time
@user_private_router.callback_query(StateFilter(RegDeliver.day))
async def get_user_day(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(day=callback.data)
    kbds = {f"{num} : 00": f"{num} : 00" for num in range(10, 21)}
    await callback.message.delete()
    await callback.message.answer(
        "Выберите удобное время", reply_markup=get_callback_btns(btns=kbds, sizes=(4,))
    )
    await callback.answer()
    await state.set_state(RegDeliver.time)


# Ловим состояние time, выходим из состояний
@user_private_router.callback_query(StateFilter(RegDeliver.time))
async def get_user_data(
    callback: types.CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
):
    await state.update_data(time=callback.data)
    await callback.message.delete()
    data = await state.get_data()
    await state.clear()
    await orm_delete_from_basket(session, user_id=data["user_id"])
    caption = (
        f"Доставка оформлена 🔥\nДетали заказа:\nАдрес: {data['addr']}\n"
        f"Дата: {data['day']}-{data['month'].rjust(2, '0')}-{datetime.now().date().year}\n"
        f"Время: {data['time']}\nНомер для связи: {data['num']}"
    )
    media, reply_murkup = await get_menu_content(
        session, level=5, menu_name="success_deliver", caption=caption
    )
    await callback.message.answer_photo(
        media.media, caption=media.caption, reply_markup=reply_murkup
    )
    await callback.answer()
