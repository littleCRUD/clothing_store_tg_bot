from sqlalchemy import BigInteger, String, Float, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):

    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )


class Banner(Base):
    "" "Создаем таблицу для image страниц" ""

    __tablename__ = "banner"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(15), unique=True)
    image: Mapped[str] = mapped_column(String(150), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)


class Category(Base):
    """Создаем таблицу для категорий товаров"""

    __tablename__ = "category"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)


class Product(Base):
    """Создаем таблицу для товаров"""

    __tablename__ = "product"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float(asdecimal=True), nullable=False)
    image: Mapped[str] = mapped_column(String(150))
    category_id: Mapped[int] = mapped_column(
        ForeignKey("category.id", ondelete="CASCADE"), nullable=False
    )

    category: Mapped["Category"] = relationship(backref="product")


class User(Base):
    """Создаем таблицу для юзеров"""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    first_name: Mapped[str] = mapped_column(String(150), nullable=True)
    last_name: Mapped[str] = mapped_column(String(150), nullable=True)
    phone: Mapped[str] = mapped_column(String(13), nullable=True)


class Basket(Base):
    """Создаем таблицу для корзины"""

    __tablename__ = "basket"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), nullable=False
    )
    quantity: Mapped[int]
    user: Mapped["User"] = relationship(backref="basket")
    product: Mapped["Product"] = relationship(backref="basket")


class Admins(Base):
    """Создаем таблицу для админов"""

    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    admin_name: Mapped[str] = mapped_column(String(150), nullable=True)
