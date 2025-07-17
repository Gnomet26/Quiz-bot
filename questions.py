from db import SessionLocal
from test_model import TestQuestion

# Bazaga ulanish
session = SessionLocal()

# Barcha savollarni olish
questions = session.query(TestQuestion).all()

# Tartibli chiqarish
for q in questions:
    print(f"{q.id}) {q.question}")
    print(f"  ✅ {q.true}")
    if q.false_1:
        print(f"  ❌ {q.false_1}")
    if q.false_2:
        print(f"  ❌ {q.false_2}")
    if q.false_3:
        print(f"  ❌ {q.false_3}")
    if q.false_4:
        print(f"  ❌ {q.false_4}")
    print()  # bo'sh qator ajratish uchun
