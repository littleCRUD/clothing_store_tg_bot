from aiogram.utils.formatting import Bold, as_list, as_marked_section


categories = ['Футболки', 'Брюки', 'Обувь']

#Caption для информационных страниц
description_for_info_pages = {
    "main": "Добро пожаловать!",
    'order': "Меню заказа товара",
    "about": "Магазин Галерея моды.\nРежим работы с 10:00 до 22:00, без выходных",
    "payment": as_marked_section(
        Bold("Варианты оплаты:"),
        "Картой в боте",
        "При получении карта/наличные",
        "В магазине",
        marker="✅ ",
    ).as_html(),
    "deliver": as_list(
        as_marked_section(
            Bold("Варианты доставки/заказа:"),
            "Доставка в течении двух дней курьером",
            "Экспресс доставка(Указать день и время когда удобно)",
            marker="✅ ",
        ),
        as_marked_section(Bold("Недоступно:"), "За пределами города", marker="❌ "),
        sep="\n----------------------\n",
    ).as_html(),
    'catalog': 'Каталог:',
    'basket': 'В корзине ничего нет!'
}
