from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData


class MenuCallBack(CallbackData, prefix="menu"):
    """Формируем меню Callback"""
    level: int
    menu_name: str
    category: int | None = None
    page: int = 1
    product_id: int | None = None

#Кнопки main меню ползователя
def get_user_main_btns(*, level: int, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    btns = {
        "Товары 👚": "catalog",
        "Корзина 🛒": "basket",
        "О нас ℹ️": "about",
        "Оплата 💰": "payment",
        "Доставка 🚚": "deliver",
    }
    for text, menu_name in btns.items():
        if menu_name == "catalog":
            keyboard.add(
                InlineKeyboardButton(
                    text=text,
                    callback_data=MenuCallBack(level=1, menu_name=menu_name).pack(),
                )
            )
        elif menu_name == "basket":
            keyboard.add(
                InlineKeyboardButton(
                    text=text,
                    callback_data=MenuCallBack(level=3, menu_name=menu_name).pack(),
                )
            )
        else:
            keyboard.add(
                InlineKeyboardButton(
                    text=text,
                    callback_data=MenuCallBack(level=level, menu_name=menu_name).pack(),
                )
            )
    return keyboard.adjust(*sizes).as_markup()

#Кнопки каталога
def get_user_catalog_btns(*, level: int, categories: list, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(
        InlineKeyboardButton(
            text="Назад",
            callback_data=MenuCallBack(level=level - 1, menu_name="main").pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="Корзина 🛒",
            callback_data=MenuCallBack(level=3, menu_name="basket").pack(),
        )
    )

    for c in categories:
        keyboard.add(
            InlineKeyboardButton(
                text=c.name,
                callback_data=MenuCallBack(
                    level=level + 1, menu_name=c.name, category=c.id
                ).pack(),
            )
        )

    return keyboard.adjust(*sizes).as_markup()

#Кнопки меню корзины
def get_user_basket(
    *,
    level: int,
    page: int | None,
    pagination_btns: dict | None,
    product_id: int | None,
    sizes: tuple[int] = (3,)
):

    keyboard = InlineKeyboardBuilder()

    if page:

        keyboard.add(
            InlineKeyboardButton(
                text="Удалить",
                callback_data=MenuCallBack(
                    level=level, menu_name="delete", product_id=product_id, page=page
                ).pack(),
            )
        )

        keyboard.add(
            InlineKeyboardButton(
                text="-1",
                callback_data=MenuCallBack(
                    level=level, menu_name="decrement", product_id=product_id, page=page
                ).pack(),
            )
        )

        keyboard.add(
            InlineKeyboardButton(
                text="+1",
                callback_data=MenuCallBack(
                    level=level, menu_name="increment", product_id=product_id, page=page
                ).pack(),
            )
        )

        keyboard.adjust(*sizes)

        row = []

        for text, menu_name in pagination_btns.items():
            if menu_name == "next":
                row.append(
                    InlineKeyboardButton(
                        text=text,
                        callback_data=MenuCallBack(
                            level=level, menu_name=menu_name, page=page + 1
                        ).pack(),
                    )
                )
            elif menu_name == "previous":
                row.append(
                    InlineKeyboardButton(
                        text=text,
                        callback_data=MenuCallBack(
                            level=level, menu_name=menu_name, page=page - 1
                        ).pack(),
                    )
                )

        keyboard.row(*row)

        row2 = [
            InlineKeyboardButton(
                text="На главную🏠",
                callback_data=MenuCallBack(level=0, menu_name="main").pack(),
            ),
            InlineKeyboardButton(
                text="Заказать",
                callback_data=MenuCallBack(level=4, menu_name="order").pack(),
            ),
        ]
        return keyboard.row(*row2).as_markup()

    else:
        keyboard.add(
            InlineKeyboardButton(
                text="На главную🏠",
                callback_data=MenuCallBack(level=0, menu_name="main").pack(),
            )
        )
        return keyboard.adjust(*sizes).as_markup()

#Кнопки действий с продуктом
def get_products_btns(
    *,
    level: int,
    category: int,
    page: int,
    pagination_btns: dict,
    product_id: int,
    sizes: tuple[int] = (2, 1)
):
    keyboard = InlineKeyboardBuilder()

    keyboard.add(
        InlineKeyboardButton(
            text="Назад",
            callback_data=MenuCallBack(level=level - 1, menu_name="main").pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="Корзина 🛒",
            callback_data=MenuCallBack(level=3, menu_name="basket").pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="Купить 💵",
            callback_data=MenuCallBack(
                level=3, menu_name="add_to_basket", product_id=product_id
            ).pack(),
        )
    )

    keyboard.adjust(*sizes)

    row = []

    for text, menu_name in pagination_btns.items():
        if menu_name == "next":
            row.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=MenuCallBack(
                        level=level,
                        menu_name=menu_name,
                        category=category,
                        page=page + 1,
                    ).pack(),
                )
            )

        elif menu_name == "previous":
            row.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=MenuCallBack(
                        level=level,
                        menu_name=menu_name,
                        category=category,
                        page=page - 1,
                    ).pack(),
                )
            )

    return keyboard.row(*row).as_markup()

#Кнопки оформления заказа
def get_order_btns(sizes: tuple[int] = (2, 2)):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text="Оплатить 💵",
            callback_data=MenuCallBack(level=5, menu_name="buy_this").pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="Закзать доставку",
            callback_data=MenuCallBack(level=5, menu_name="deliver_this").pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="Корзина 🛒",
            callback_data=MenuCallBack(level=3, menu_name="basket").pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="На главную🏠",
            callback_data=MenuCallBack(level=0, menu_name="main").pack(),
        )
    )

    return keyboard.adjust(*sizes).as_markup()

#Кнопки меню оплаченного товара
def get_buy_btns(sizes: tuple[int] = (1,)):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text="На главную🏠",
            callback_data=MenuCallBack(level=0, menu_name="main").pack(),
        )
    )
    return keyboard.adjust(*sizes).as_markup()

#Кнопки оформления доставки
def get_deliver_btns(level: int, sizes: tuple[int] = (1, 2)):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(
        InlineKeyboardButton(
            text="Оформить доставку 🚚",
            callback_data=MenuCallBack(level=level, menu_name="reg_deliver").pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="Назад ◀️",
            callback_data=MenuCallBack(level=4, menu_name="order").pack(),
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="На главную🏠",
            callback_data=MenuCallBack(level=0, menu_name="main").pack(),
        )
    )

    return keyboard.adjust(*sizes).as_markup()

#Функция создания обычной inline клавиатуры с минимальным набором параметров 
def get_callback_btns(*, btns: dict[str, str], sizes: tuple[int] = (2,)):
    '''
    Пример:
        get_callback_btns(
        btns={
            "Удалить": f"delete_",
            "Изменить": f"change_",
            },
            sizes=(2,)
        )    
    '''
    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()
