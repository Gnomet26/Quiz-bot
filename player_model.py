from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Player(Base):
    __tablename__ = "players"

    telegram_id = Column(String(64), primary_key=True)  # unikal Telegram ID
    first_name = Column(String(100))
    last_name = Column(String(100))

    true_answers = Column(Integer, default=0)
    false_answers = Column(Integer)
    current_question = Column(Integer, default=1)
    total_questions = Column(Integer)

    def __repr__(self):
        return f"<Player {self.telegram_id} - {self.first_name}>"
