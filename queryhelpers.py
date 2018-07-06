"""
Commonly-used queries
"""
from sqlalchemy.exc import SQLAlchemyError
from setup import Category, Item
import bleach


def getCategories(session):
    """
    Retrieve all categories.
    :param session: (DBSession) SQLAlchemy session
    :return:
    List of Category objects.
    """
    try:
        categories = (session.query(Category)
                      .order_by(Category.name)
                      .all())
    except SQLAlchemyError:
        return False
    return categories


def getItems(session):
    """
       Retrieve all items.
       :param session: (DBSession) SQLAlchemy session
       :return:
       List of Item objects from the greatest to lowest id
       """
    try:
        items = (session.query(Item)
                 .filter(Item.category_id == Category.id)
                 .order_by(Item.id.desc())
                 .all())
    except SQLAlchemyError:
        return False
    return items


def getCategory(category_name, session):
        """
        Retrieve a category based on category name
        :param category_name: (string)
        :param session: (DBSession) SQLAlchemy session
        :return:
       Category object.
        """
        try:
            category = (session.query(Category)
                        .filter_by(name=bleach.clean(category_name))
                        .one())
        except SQLAlchemyError:
            return False
        return category


def getCategoryItems(category_id, session):
    """
    Retrieve a category's items based on category id.
    :param category_id: (integer)
    :param session: (DBSession) SQLAlchemy session
    :return:
   Category object.
    """
    try:
        items = (session.query(Item)
                 .filter_by(category_id=category_id)
                 .filter(Item.category_id == Category.id)
                 .order_by(Item.id.desc())
                 .all())
    except SQLAlchemyError:
        return False
    return items


def getItem(category_id, item_name, session):
    """
    Retrieve item based on category id and item name.
    :param category_id: (integer) Category.id
    :param item_name: (string) Item.name
    :param session: (DBSession) SQLAlchemy session
    :return:
    Item object.
    """
    try:
        item = (session.query(Item)
                .filter_by(category_id=category_id,
                           name=bleach.clean(item_name.lower()))
                .one())
    except SQLAlchemyError:
        return False
    return item
