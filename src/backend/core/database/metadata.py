from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

__all__ = ("Base",)

metadata = MetaData(
    naming_convention={
        "pk": "pk_%(table_name)s",
        "fk": "fk_%(table_name)s_%(column_0_label)s_%(referred_table_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "uq": "uq_%(table_name)s_%(column_0_label)s",
        "ix": "ix_%(table_name)s_%(column_0_label)s",
    },
)


class Base(DeclarativeBase):
    metadata = metadata
