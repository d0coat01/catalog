from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from setup import Base, User

engine = create_engine('sqlite:///catalog.db', pool_pre_ping=True)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

# Test User

def test_user():
    session = DBSession()