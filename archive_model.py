# archive_model.py

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Archive(Base):
    __tablename__ = "archive"

    id = Column(Integer, primary_key=True, autoincrement=True)  # Har bir qatnashuvga unikal ID
    telegram_id = Column(String(64))  # Playerdagi bilan bir xil
    first_name = Column(String(100))
    last_name = Column(String(100))

    true_answers = Column(Integer, default=0)
    false_answers = Column(Integer)
    current_question = Column(Integer)
    total_questions = Column(Integer)

    completed_at = Column(DateTime, default=datetime.utcnow)  # Test tugagan vaqt

    def __repr__(self):
        return f"<Archive {self.telegram_id} - {self.first_name} {self.true_answers}/{self.total_questions}>"
