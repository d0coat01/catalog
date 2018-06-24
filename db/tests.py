from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from setup import Base, User

engine = create_engine('sqlite:///catalog.db', pool_pre_ping=True)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
test_user = {"email": "test@test.com", "password": "password"}
# Test User
# Run suite of tests.
def run_tests():
    cleanup()
    # Primary tests
    create_user(test_user)
    cleanup()

def cleanup():
    new_user = session.query(User).filter_by(email=test_user["email"]).one()
    session.delete(new_user)
    session.commit()
# create user
def create_user(user):
    new_user = User(email=user["email"], password=user["password"])
    session.add(new_user)
    session.commit()
    created_user = session.query(User).filter_by(email=user["email"]).exists()
    try:
        print "."
    except:
        print "Unable to create test user."

if __name__ == '__main__':
    run_tests()