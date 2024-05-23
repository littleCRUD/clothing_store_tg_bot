import math
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from database.models import Banner, Basket, Category, Product, User, Admins


class Paginator:
    """Создаем пагинатор"""

    def __init__(self, array: list | tuple, page: int = 1, per_page: int = 1):
        self.array = array
        self.per_page = per_page
        self.page = page
        self.len = len(self.array)
        self.pages = math.ceil(self.len / self.per_page)

    def __get_slice(self):
        start = (self.page - 1) * self.per_page
        stop = start + self.per_page
        return self.array[start:stop]

    def get_page(self):
        page_items = self.__get_slice()
        return page_items

    def has_next(self):
        if self.page < self.pages:
            return self.page + 1
        return False

    def has_previous(self):
        if self.page > 1:
            return self.page - 1
        return False

    def get_next(self):
        if self.page < self.pages:
            self.page += 1
            return self.get_page()
        raise IndexError("Next page does not exist. Use has_next() to check before.")

    def get_previous(self):
        if self.page > 1:
            self.page -= 1
            return self.__get_slice()
        raise IndexError(
            "Previous page does not exist. Use has_previous() to check before."
        )


############### Работа с баннерами (инфо страниц) бота ###############


# Добавляем описание для инфо страниц бота
async def orm_add_banner_description(session: AsyncSession, data: dict):
    query = select(Banner)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all(
        [
            Banner(name=name, description=description)
            for name, description in data.items()
        ]
    )
    await session.commit()


# Изменяем картинку инфо страницы
async def orm_change_banner_image(session: AsyncSession, name: str, image: str):
    query = update(Banner).where(Banner.name == name).values(image=image)
    await session.execute(query)
    await session.commit()


# Получем баннер из БД
async def orm_get_banner(session: AsyncSession, page: str):
    query = select(Banner).where(Banner.name == page)
    result = await session.execute(query)
    return result.scalar()


# Получем перечень инфо страниц бота
async def orm_get_info_pages(session: AsyncSession):
    query = select(Banner)
    result = await session.execute(query)
    return result.scalars().all()


################### Работа с категориями товаров ###################


# Получем категорию из БД
async def orm_get_categories(session: AsyncSession):
    query = select(Category)
    result = await session.execute(query)
    return result.scalars().all()


# Создаем категорию
async def orm_create_categories(session: AsyncSession, categories: list):
    query = select(Category)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Category(name=name) for name in categories])
    await session.commit()


################# Админка: добавить/изменить/удалить товар #######################
# Добавляем товар в БД
async def orm_add_product(session: AsyncSession, data: dict) -> None:
    obj = Product(
        name=data["name"],
        description=data["description"],
        price=float(data["price"]),
        image=data["image"],
        category_id=int(data["category"]),
    )
    session.add(obj)
    await session.commit()


# Получаем все продукты в категории из БД
async def orm_get_products(session: AsyncSession, category_id):
    query = select(Product).where(Product.category_id == int(category_id))
    result = await session.execute(query)
    return result.scalars().all()


# Получаем конткретный продукт из БД
async def orm_get_product(session: AsyncSession, product_id: int):
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    return result.scalar()


# Меняем данные продукта
async def orm_update_product(session: AsyncSession, product_id: int, data) -> None:
    query = (
        update(Product)
        .where(Product.id == product_id)
        .values(
            name=data["name"],
            description=data["description"],
            price=float(data["price"]),
            image=data["image"],
            category_id=int(data["category"]),
        )
    )
    await session.execute(query)
    await session.commit()


# Удаляем продукт из БД
async def orm_delete_product(session: AsyncSession, product_id: int):
    query = delete(Product).where(Product.id == product_id)
    await session.execute(query)
    await session.commit()


##################### Добавляем юзера в БД #####################################


async def orm_add_user(
    session: AsyncSession,
    user_id: int,
    first_name: str | None = None,
    last_name: str | None = None,
    phone: str | None = None,
):
    query = select(User).where(User.user_id == user_id)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            User(
                user_id=user_id, first_name=first_name, last_name=last_name, phone=phone
            )
        )
        await session.commit()


##############Админка: добавить/изменить/удалить админа, показать список админов############


# Получаем список всех админов
async def orm_get_all_admins(
    session: AsyncSession,
    admin_id: int | None = None,
):
    if admin_id is not None:
        query = select(Admins).where(Admins.admin_id == admin_id)
        result = await session.execute(query)
        return result.scalars().all()
    query = select(Admins)
    result = await session.execute(query)
    return result.scalars().all()


# Добавляем нового админа
async def orm_add_admin(session: AsyncSession, data: dict):
    admin_id = int(data["admin_id"])
    admin_name = data["username"]
    query = select(Admins).where(Admins.admin_id == admin_id)
    result = await session.execute(query)
    if result.first() is None:
        session.add(Admins(admin_id=admin_id, admin_name=admin_name))
        await session.commit()
    else:
        query = (
            update(Admins)
            .where(Admins.admin_id == admin_id)
            .values(admin_name=admin_name)
        )
        await session.execute(query)
        await session.commit()


# Удаляем админа
async def orm_delete_admin(session: AsyncSession, admin_id: int):
    query = delete(Admins).where(Admins.admin_id == admin_id)
    await session.execute(query)
    await session.commit()


######################## Работа с корзинами #######################################


# Добавить товар в корзину
async def orm_add_to_basket(session: AsyncSession, user_id: int, product_id: int):
    query = (
        select(Basket)
        .where(Basket.user_id == user_id, Basket.product_id == product_id)
        .options(joinedload(Basket.product))
    )
    cart = await session.execute(query)
    cart = cart.scalar()
    if cart:
        cart.quantity += 1
        await session.commit()
        return cart
    else:
        session.add(Basket(user_id=user_id, product_id=product_id, quantity=1))
        await session.commit()


# Получить корзину для юзера
async def orm_get_user_basket(session: AsyncSession, user_id):
    query = (
        select(Basket)
        .filter(Basket.user_id == user_id)
        .options(joinedload(Basket.product))
    )
    result = await session.execute(query)
    return result.scalars().all()


# Удалить товар из корзины
async def orm_delete_from_basket(
    session: AsyncSession,
    user_id: int,
    product_id: int | None = None,
):
    if product_id:
        query = delete(Basket).where(
            Basket.user_id == user_id, Basket.product_id == product_id
        )
    else:
        query = delete(Basket).where(Basket.user_id == user_id)
    await session.execute(query)
    await session.commit()


# Менем количетсво товаров в корзине
async def orm_reduce_product_in_basket(
    session: AsyncSession, user_id: int, product_id: int
):
    query = (
        select(Basket)
        .where(Basket.user_id == user_id, Basket.product_id == product_id)
        .options(joinedload(Basket.product))
    )
    basket = await session.execute(query)
    basket = basket.scalar()

    if not basket:
        return
    if basket.quantity > 1:
        basket.quantity -= 1
        await session.commit()
        return True
    else:
        await orm_delete_from_basket(session, user_id, product_id)
        await session.commit()
        return False
