# coding:utf-8

from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.dialects.mysql import BIT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DeclarativeBase = declarative_base()


class User(DeclarativeBase):
    __tablename__ = 'users'
    id = Column('id', Integer, primary_key=True)
    name = Column('name', String(20))
    phone = Column('phone', String(20), unique=True)
    password = Column('password', String(100))
    rank = Column('rank', String(30))
    email = Column('email', String(50))
    last_login = Column('last_login', DateTime)
    last_ip = Column('last_ip', String(20))
    group = Column('group', String(20))


class LoginInfo(DeclarativeBase):
    __tablename__ = 'login_info'
    id = Column('id', Integer, primary_key=True)
    user_id = Column('user_id', Integer)
    time = Column('time', DateTime)
    ip = Column('ip', String(20))


engine = create_engine('mysql+mysqldb://root:mpb.SQL159753@127.0.0.1:3306/test?charset=utf8',
                       encoding='utf8',
                       echo=False,
                       pool_recycle=5, )
Session = sessionmaker(bind=engine)
db_session = Session()

if __name__ == "__main__":
    pass
