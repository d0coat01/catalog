from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import hashlib
import random, string


Base = declarative_base()

secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))


# TODO: Create tests for user table
class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    email = Column(String(300), unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    items = relationship("Item", backref="user")



# TODO: Create Category


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


# TODO: Create Item
class Item(Base):
    __tablename__ = "item"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True)
    description = Column(String)
    category_id = Column(Integer, ForeignKey("category.id"))
    user_id = Column(Integer, ForeignKey("user.id"))

engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)