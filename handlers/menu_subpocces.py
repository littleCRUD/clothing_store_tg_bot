from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import InputMediaPhoto
from database.orm_query import (
    Paginator,
    orm_add_to_basket,
    orm_delete_from_basket,
    orm_get_banner,
    orm_get_categories,
    orm_get_user_basket,
    orm_get_products,
    orm_reduce_product_in_basket,
)
from kbds.inline import (
    get_buy_btns,
    get_deliver_btns,
    get_order_btns,
    get_products_btns,
    get_user_basket,
    get_user_catalog_btns,
    get_user_main_btns,
)


# Осноновное меню пользователя, стартовый уровнь меню callback
async def main_menu(session, level, menu_name):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    kbds = get_user_main_btns(level=level)
    return image, kbds


# Меню каталога, первый уровень меню callback
async def catalog(session, level, menu_name):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    categories = await orm_get_categories(session=session)
    kbds = get_user_catalog_btns(level=level, categories=categories)

    return image, kbds


# Кнопки для пагинации
def pages(paginator: Paginator):
    btns = dict()
    if paginator.has_previous():
        btns["⏮️ Пред."] = "previous"
    if paginator.has_next():
        btns["След. ⏭️"] = "next"
    return btns


# Меню выбора продуктов в категории
async def products(session: AsyncSession, level: int, category: int, page: int):
    _products = await orm_get_products(session, category_id=category)
    paginator = Paginator(_products, page=page)
    product = paginator.get_page()[0]

    image = InputMediaPhoto(
        media=product.image,
        caption=f"<strong>{product.name}\
                </strong>\n{product.description}\nстоимость: {round(product.price, 2)}\n\
                <strong>Товар {paginator.page} из {paginator.pages}</strong>",
    )

    pagination_btns = pages(paginator)

    kbds = get_products_btns(
        level=level,
        category=category,
        page=page,
        pagination_btns=pagination_btns,
        product_id=product.id,
    )

    return image, kbds


# Меню корзины
async def basket(session, level, menu_name, page, user_id, product_id):
    if menu_name == "delete":
        await orm_delete_from_basket(session, user_id, product_id)
        if page > 1:
            page -= 1
    elif menu_name == "decrement":
        is_basket = await orm_reduce_product_in_basket(session, user_id, product_id)
        if page > 1 and not is_basket:
            page -= 1
    elif menu_name == "increment":
        await orm_add_to_basket(session=session, user_id=user_id, product_id=product_id)

    baskets = await orm_get_user_basket(session, user_id)

    if not baskets:
        banner = await orm_get_banner(session, "basket")
        image = InputMediaPhoto(
            media=banner.image, caption=f"<strong>{banner.description}</strong>"
        )

        kbds = get_user_basket(
            level=level,
            page=None,
            pagination_btns=None,
            product_id=None,
        )

    else:
        paginator = Paginator(baskets, page=page)

        cart = paginator.get_page()[0]

        cart_price = round(cart.quantity * cart.product.price, 2)
        total_price = round(
            sum(cart.quantity * cart.product.price for cart in baskets), 2
        )
        image = InputMediaPhoto(
            media=cart.product.image,
            caption=f"<strong>{cart.product.name}</strong>\n{round(cart.product.price, 2)} x "\
                    f"{cart.quantity} = {cart_price}\nТовар {paginator.page} из {paginator.pages}"\
                    f"в корзине.\nОбщая стоимость товаров в корзине {total_price}"
        )

        pagination_btns = pages(paginator)

        kbds = get_user_basket(
            level=level,
            page=page,
            pagination_btns=pagination_btns,
            product_id=cart.product.id,
        )

    return image, kbds


# Меню оформления заказа
async def order(session: AsyncSession, user_id: int):
    banner = await orm_get_banner(session, "main")
    baskets = await orm_get_user_basket(session, user_id)
    total_price = round(
        sum(basket.quantity * basket.product.price for basket in baskets), 2
    )
    image = InputMediaPhoto(
        media=banner.image, caption=f"Заказ на сумму:\n{total_price}\nСформирован!"
    )
    kbds = get_order_btns()
    return image, kbds


# Меню покупки заказа
async def success_buy(
    session: AsyncSession,
    level: int,
    menu_name: str,
    user_id: int,
    caption: str,
):

    if menu_name == "buy_this":
        await orm_delete_from_basket(session, user_id)
        banner = await orm_get_banner(session, "main")
        image = InputMediaPhoto(
            media=banner.image, caption="<strong>Заказ оплачен🔥</strong>"
        )
        kbds = get_buy_btns()
        return image, kbds
    elif menu_name == "deliver_this":
        banner = await orm_get_banner(session, "main")
        image = InputMediaPhoto(
            media=banner.image, caption="<strong>Меню оформления доствки</strong>"
        )
        kbds = get_deliver_btns(level=level)
        return image, kbds
    elif menu_name == "success_deliver":
        banner = await orm_get_banner(session, "main")
        image = InputMediaPhoto(
            media=banner.image, caption=f"<strong>{caption}</strong>"
        )
        kbds = get_buy_btns()
        return image, kbds



# Строим меню CallBack
async def get_menu_content(
    session: AsyncSession,
    level: int,
    menu_name: str,
    category: int | None = None,
    page: int | None = None,
    product_id: int | None = None,
    user_id: int | None = None,
    caption: str | None = None,
):

    if level == 0:
        return await main_menu(session, level, menu_name)
    elif level == 1:
        return await catalog(session, level, menu_name)
    elif level == 2:
        return await products(session, level, category, page)
    elif level == 3:
        return await basket(session, level, menu_name, page, user_id, product_id)
    elif level == 4:
        return await order(session, user_id)
    elif level == 5:
        return await success_buy(session, level, menu_name, user_id, caption)
