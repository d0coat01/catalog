from sqlalchemy import (Column, ForeignKey, Integer,
                        String, Boolean, UniqueConstraint)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    email = Column(String(300), unique=True, nullable=False)
    username = Column(String(100))
    is_admin = Column(Boolean, default=False)
    items = relationship("Item", backref="user")


class Category(Base):
    __tablename__ = "category"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    label = Column(String(100), nullable=False)
    items = relationship("Item", backref="category")

    def __init__(self, name):
        self.label = name
        self.name = name.lower()

    @property
    def serialize(self):
        return {
            'name': self.name,
            'label': self.label,
            'id': self.id,
        }

    @property
    def serialize_items(self):
        items = [r.serialize for r in self.items]
        return {
            'name': self.name,
            'label': self.label,
            'id': self.id,
            'items': items

        }


class Item(Base):
    __tablename__ = "item"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    label = Column(String(200), nullable=False)
    description = Column(String)
    category_id = Column(Integer, ForeignKey("category.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    __table_args__ = (
        UniqueConstraint('category_id', 'name',  name='unique_index_1'),
    )

    def validate_name(self, name):
        if len(name) < 1:
            raise ValueError('Name too short')
        return name

    @property
    def serialize(self):
        return {
            'name': self.name,
            'label': self.label,
            'description': self.description,
            'id': self.id,
        }


engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)
