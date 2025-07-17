from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# MySQL uchun ulanish
engine = create_engine('mysql+mysqlconnector://root:Qweasd123@localhost:3306/quizbot', echo=False)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
