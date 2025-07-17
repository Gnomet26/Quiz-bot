from sqlalchemy import Column, Integer, String
from db import Base

class TestQuestion(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(String(512), nullable=False)
    true = Column(String(256), nullable=False)
    false_1 = Column(String(256), nullable=True)
    false_2 = Column(String(256), nullable=True)
    false_3 = Column(String(256), nullable=True)
    false_4 = Column(String(256), nullable=True)
