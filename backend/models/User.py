from sqlalchemy import Column, Integer, String
from database.db import Base2


class User(Base2):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(String)
    last_login = Column(String)


    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at,
            "last_login": self.last_login
        }
    

    def from_dict(self, data):
        for field in ['username', 'email', 'hashed_password', 'created_at', 'last_login']:
            if field in data:
                setattr(self, field, data[field])

    