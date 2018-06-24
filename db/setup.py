from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import hashlib
import random, string
from itsdangerous import(TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)


Base = declarative_base()

secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))

# TODO: Create tests for user table
class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    email = Column(String(300), unique=True, nullable=False)
    password = Column(String(64), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))

    def __init__(self, email, password):
        self.email = email
        self.password = self.encrypt_password(password)

    def encrypt_password(self, password):
        return hashlib.sha224(password).hexdigest()

    def verify_password(self, password):
        return self.password == hashlib.sha224(password).hexdigest()[0:63]

    def generate_auth_token(self, expiration=600):
        s = Serializer(secret_key, expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_token(token):
        s = Serializer(secret_key)
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None
        except BadSignature:
            return None
        return data['id']

# TODO: Create Catalog
# TODO: Create Item
engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)