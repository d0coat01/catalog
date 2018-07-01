from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
# append db directory to python path so we can import sqlalchemy classes.
sys.path.append('./db')
from setup import Base, User, Category, Item

engine = create_engine('sqlite:///catalog.db', pool_pre_ping=True)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

#Add dummy user
User1 = User(username="Daniel Coats", email="danielcoats02@gmail.com", is_admin=True)
session.add(User1)
session.commit()

#Add categories
C1 = Category(name="Cats")
session.add(C1)
session.commit()
C2 = Category(name="Coffee")
session.add(C2)
session.commit()
C3 = Category(name="Japan")
session.add(C3)
session.commit()
C4 = Category(name="Home")
session.add(C4)
session.commit()
C5 = Category(name="Dogs")
session.add(C5)
session.commit()

#Add items
I1 = Item(name="buster", label="Buster", description = "A real rascal.", category_id=1, user_id=1)
session.add(I1)
session.commit()
I2 = Item(name="that place with a really long name that might break japan as we know it", label="That place with a really long name that might break japan as we know it", description = "Ramen here.", category_id=3, user_id=1)
session.add(I2)
session.commit()
I3 = Item(name="mr. kitty", label="Mr. Kitty", description = "The coolest cat.", category_id=1, user_id=1)
session.add(I3)
session.commit()
I4 = Item(name="boxer", label="Boxer", description = "A tough guy.", category_id=5, user_id=1)
session.add(I4)
session.commit()
I5 = Item(name="ikea bed frame", label="IKEA Bed Frame", description = "The best start to your day is a good nights sleep. Our sturdy double beds in different styles give you comfort and quality so you wake up with a smile. Many have smart features like built-in storage or are sized so you can slide boxes underneath. Look around our website to find what else you need, like a mattress or pillows, to complete the comfy bed of your dreams. The best start to your day is a good nights sleep. Our sturdy double beds in different styles give you comfort and quality so you wake up with a smile. Many have smart features like built-in storage or are sized so you can slide boxes underneath. Look around our website to find what else you need, like a mattress or pillows, to complete the comfy bed of your dreams.", category_id=4, user_id=1)
session.add(I5)
session.commit()