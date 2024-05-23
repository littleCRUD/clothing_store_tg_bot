from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.ext.asyncio import AsyncSession
from filters.chat_types import ChatTypeFilter, IsAdmin
from kbds.reply import get_keyboard
from kbds.inline import get_callback_btns

from database.orm_query import (
    orm_add_admin,
    orm_delete_admin,
    orm_change_banner_image,
    orm_get_all_admins,
    orm_get_categories,
    orm_add_product,
    orm_delete_product,
    orm_get_info_pages,
    orm_get_product,
    orm_get_products,
    orm_update_product,
)


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


# Создаем клавиатуру админа
ADMIN_KB = get_keyboard(
    "Добавить товар",
    "Открыть каталог",
    "Добавить/Изменить баннер",
    "Выйти из режима admin",
    "Admins list",
    placeholder="Выберите действие",
    sizes=(2, 1, 2),
)


# Ловим команду admin
@admin_router.message(Command("admin"))
async def admin_features(message: types.Message) -> None:
    await message.answer("Что хотите сделать?", reply_markup=ADMIN_KB)


# Хэндлер выхода из режима admin
@admin_router.message(F.text == "Выйти из режима admin")
async def admin_out(message: types.Message) -> None:
    await message.answer(
        "Для запуска введите /start", reply_markup=types.ReplyKeyboardRemove()
    )


# Хэндлер открытия каталога
@admin_router.message(F.text == "Открыть каталог")
async def admin_features2(message: types.Message, session: AsyncSession):
    categories = await orm_get_categories(session)
    btns = {category.name: f"category_{category.id}" for category in categories}
    await message.answer(
        "Выберите категорию", reply_markup=get_callback_btns(btns=btns)
    )


# Ловим выбранную категорию, получаем список товаров в ней
@admin_router.callback_query(F.data.startswith("category_"))
async def starring_at_product(callback: types.CallbackQuery, session: AsyncSession):
    category_id = callback.data.split("_")[-1]
    for product in await orm_get_products(session, int(category_id)):
        await callback.message.answer_photo(
            product.image,
            caption=f"<strong>{product.name}\
                    </strong>\n{product.description}\nСтоимость: {round(product.price, 2)}",
            reply_markup=get_callback_btns(
                btns={
                    "Удалить": f"delete_{product.id}",
                    "Изменить": f"change_{product.id}",
                },
                sizes=(2,),
            ),
        )
    await callback.answer()
    await callback.message.answer("ОК, вот список товаров ⏫")


# Хндлер удаления товара
@admin_router.callback_query(F.data.startswith("delete_"))
async def delete_product_callback(callback: types.CallbackQuery, session: AsyncSession):
    product_id = callback.data.split("_")[-1]
    await orm_delete_product(session, int(product_id))
    await callback.answer("Товар удален")
    await callback.message.answer("Товар удален!")


########################Работа с админами (удалить/добавить/изменить)############################


# Ловим команду Admins list, выводим меню список админов, удалить/добавить нового админа
@admin_router.message(F.text == "Admins list")
async def get_admins_list(message: types.Message):
    btns = {
        "Список админов": "adminls_",
        "Добавить нового админа": "addadmin_",
    }
    await message.answer(
        "Выберите действие", reply_markup=get_callback_btns(btns=btns), sizes=(2, 1)
    )


# Выводим список админов
@admin_router.callback_query(F.data.startswith("adminls_"))
async def get_all_admins(callback: types.CallbackQuery, session: AsyncSession):
    for admin in await orm_get_all_admins(session):
        await callback.message.answer(
            text=f"<strong>id: {admin.admin_id}</strong>\n{admin.admin_name}",
            reply_markup=get_callback_btns(
                btns={
                    "Удалить": f"admin_delete_{admin.admin_id}",
                    "Изменить имя": f"admin_change_{admin.admin_id}",
                },
                sizes=(2,),
            ),
        )
    await callback.answer()
    await callback.message.answer("ОК, вот список админов ⏫", reply_markup=ADMIN_KB)


# Удялем админа
@admin_router.callback_query(F.data.startswith("admin_delete_"))
async def delete_admin_callback(callback: types.CallbackQuery, session: AsyncSession):
    admin_id = callback.data.split("_")[-1]
    await orm_delete_admin(session, int(admin_id))
    await callback.answer("Админ удален")
    await callback.message.answer("Админ удален!")


# Изменяем name админа
@admin_router.callback_query(StateFilter(None), F.data.startswith("admin_change_"))
async def change_admin_callback(callback: types.CallbackQuery, state: FSMContext):
    admin_id = callback.data.split("_")[-1]
    await state.update_data(admin_id=admin_id)
    await callback.message.answer(
        "Введите новое username", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddAdmin.username)
    await callback.answer()


#####################Мнкро FSM  для добавления нового админа##############################


class AddAdmin(StatesGroup):
    """Шаги состояний добавления админа"""

    admin_id = State()
    username = State()


# Ловим команду addadmin_, встаем в состояние admin_id
@admin_router.callback_query(StateFilter(None), F.data.startswith("addadmin_"))
async def add_admin(callback: types.CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer(
        "Введите user_id нового админа",
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await callback.answer()
    await state.set_state(AddAdmin.admin_id)


# Ловим состояние admin_id, сохраняем id, встаемв состояние username
@admin_router.message(StateFilter(AddAdmin.admin_id), F.text)
async def add_admin_id(message: types.Message, state: FSMContext):
    await state.update_data(admin_id=message.text)
    await message.answer("Придумайте username для нового адимнистратора")
    await state.set_state(AddAdmin.username)


# Ловим состояние username, выходим из состояний
@admin_router.message(StateFilter(AddAdmin.username), F.text)
async def add_admin_username(
    message: types.Message, state: FSMContext, session: AsyncSession
) -> None:
    await state.update_data(username=message.text)
    data = await state.get_data()
    await orm_add_admin(session, data)
    await message.answer("Админ добавлен/изменен", reply_markup=ADMIN_KB)
    await state.clear()


################# Микро FSM для загрузки/изменения баннеров ############################


class AddBanner(StatesGroup):
    """Шаги состояний для добавления картинки баннера"""

    image = State()


# Отправляем перечень информационных страниц бота, встаем в состояние отправки photo
@admin_router.message(StateFilter(None), F.text == "Добавить/Изменить баннер")
async def add_image2(message: types.Message, state: FSMContext, session: AsyncSession):
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    await message.answer(
        f"Отправьте фото баннера.\nВ описании укажите для какой страницы:\
                         \n{', '.join(pages_names)}"
    )
    await state.set_state(AddBanner.image)


@admin_router.message(AddBanner.image, F.photo)
async def add_banner(message: types.Message, state: FSMContext, session: AsyncSession):
    image_id = message.photo[-1].file_id
    for_page = message.caption.strip()
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    if for_page not in pages_names:
        await message.answer(
            f"Введите нормальное название страницы, например:\
                         \n{', '.join(pages_names)}"
        )
        return
    await orm_change_banner_image(
        session,
        for_page,
        image_id,
    )
    await message.answer("Баннер добавлен/изменен.")
    await state.clear()


# Ловим некоррекный ввод
@admin_router.message(AddBanner.image)
async def add_banner2(message: types.Message):
    await message.answer("Отправьте фото баннера или отмена")


######################### FSM для дабавления/изменения товаров админом ###################


class AddProduct(StatesGroup):
    """Шаги состояний для добавления продукта"""

    name = State()
    description = State()
    category = State()
    price = State()
    image = State()
    product_for_change = None

    texts = {
        "AddProduct:name": "Введите название заново:",
        "AddProduct:description": "Введите описание заново:",
        "AddProduct:category": "Выберите категорию  заново ⬆️",
        "AddProduct:price": "Введите стоимость заново:",
        "AddProduct:image": "Этот стейт последний, поэтому...",
    }


# Меняем инфо продукта
@admin_router.callback_query(StateFilter(None), F.data.startswith("change_"))
async def change_product_callback(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    product_id = callback.data.split("_")[-1]
    product_for_change = await orm_get_product(session, int(product_id))
    AddProduct.product_for_change = product_for_change
    await callback.answer()
    await callback.message.answer(
        "Введите название товара", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddProduct.name)


# Хендлер добавления товара
@admin_router.message(StateFilter(None), F.text == "Добавить товар")
async def add_product(message: types.Message, state: FSMContext) -> None:
    await message.answer(
        "Введите название товара", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddProduct.name)


# Ловим команду отмена
@admin_router.message(StateFilter("*"), Command("отмена"))
@admin_router.message(StateFilter("*"), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    if AddProduct.product_for_change:
        AddProduct.product_for_change = None
    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KB)


# Ловим команду назад
@admin_router.message(StateFilter("*"), Command("назад"))
@admin_router.message(StateFilter("*"), F.text.casefold() == "назад")
async def back_step_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state()

    if current_state == AddProduct.name:
        await message.answer(
            'Предыдущего шага нет, или введите название товара или напишите "отмена"'
        )
        return

    previous = None
    for step in AddProduct.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(
                f"Ок, вы вернулись к прошлому шагу \n {AddProduct.texts[previous.state]}"
            )
            return
        previous = step


# Ловим данные для состояния name продукта, встаем в состояние description
@admin_router.message(AddProduct.name, F.text)
async def add_name(message: types.Message, state: FSMContext) -> None:
    if message.text == "." and AddProduct.product_for_change:
        await state.update_data(name=AddProduct.product_for_change.name)
    else:
        if 4 >= len(message.text) >= 150:
            await message.answer(
                "Название товара не должно превышать 150 символов\n"\
                "или быть менее 5ти символов. \n Введите заново"
            )
            return
        await state.update_data(name=message.text)
    await message.answer("Введите описание товара")
    await state.set_state(AddProduct.description)


# Ловим некоректный ввод name
@admin_router.message(AddProduct.name)
async def add_name2(message: types.Message):
    await message.answer("Вы ввели не допустимые данные, введите текст названия товара")


# Ловим состояние description продукта, встаем в состояние category
@admin_router.message(AddProduct.description, F.text)
async def add_description(
    message: types.Message, state: FSMContext, session: AsyncSession
) -> None:
    if message.text == "." and AddProduct.product_for_change:
        await state.update_data(description=AddProduct.product_for_change.description)
    else:
        if 4 >= len(message.text):
            await message.answer("Слишком короткое описание. \n Введите заново")
            return
        await state.update_data(description=message.text)
    categories = await orm_get_categories(session)
    btns = {category.name: str(category.id) for category in categories}
    await message.answer(
        "Выберите категорию", reply_markup=get_callback_btns(btns=btns)
    )
    await state.set_state(AddProduct.category)


# Хендлер для отлова некорректных вводов для состояния description
@admin_router.message(AddProduct.description)
async def add_description2(message: types.Message):
    await message.answer("Вы ввели не допустимые данные, введите текст описания товара")


# Ловим данные для состояния выбора категории, встаем в состояние ввода price
@admin_router.callback_query(AddProduct.category)
async def category_choice(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
):
    if int(callback.data) in [
        category.id for category in await orm_get_categories(session)
    ]:
        await callback.answer()
        await state.update_data(category=callback.data)
        await callback.message.answer("Теперь введите цену товара.")
        await state.set_state(AddProduct.price)
    else:
        await callback.message.answer("Выберите катеорию из кнопок.")
        await callback.answer()


# Ловим любые некорректные действия, кроме нажатия на кнопку выбора категории
@admin_router.message(AddProduct.category)
async def category_choice2(message: types.Message):
    await message.answer("'Выберите катеорию из кнопок.'")


# Ловим данные для состояние price, встаеем в состояние image
@admin_router.message(AddProduct.price, F.text)
async def add_price(message: types.Message, state: FSMContext):
    if message.text == "." and AddProduct.product_for_change:
        await state.update_data(price=AddProduct.product_for_change.price)
    else:
        try:
            float(message.text)
        except ValueError:
            await message.answer("Введите корректное значение цены")
            return

        await state.update_data(price=message.text)
    await message.answer("Загрузите изображение товара")
    await state.set_state(AddProduct.image)


# Хендлер для отлова некорректного ввода для состояния price
@admin_router.message(AddProduct.price)
async def add_price2(message: types.Message):
    await message.answer("Вы ввели не допустимые данные, введите стоимость товара")


# Ловим данные для состояние image, выходим из состояний
@admin_router.message(AddProduct.image, or_f(F.photo, F.text == "."))
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text and message.text == "." and AddProduct.product_for_change:
        await state.update_data(image=AddProduct.product_for_change.image)

    elif message.photo:
        await state.update_data(image=message.photo[-1].file_id)
    else:
        await message.answer("Отправьте фото одежды")
        return
    data = await state.get_data()
    try:
        if AddProduct.product_for_change:
            await orm_update_product(session, AddProduct.product_for_change.id, data)
        else:
            await orm_add_product(session, data)
        await message.answer("Товар добавлен/изменен", reply_markup=ADMIN_KB)
        await state.clear()

    except Exception as e:
        await message.answer(
            f"Ошибка: \n{str(e)}\n",
            reply_markup=ADMIN_KB,
        )
        await state.clear()

    AddProduct.product_for_change = None


# Ловим все прочее некорректное поведение для этого состояния
@admin_router.message(AddProduct.image)
async def incorrect_image(message: types.Message):
    await message.answer("Отправьте фото одежды")
