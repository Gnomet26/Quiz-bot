from db import SessionLocal, engine, Base
from sqlalchemy import inspect
from test_model import TestQuestion  # ← endi test_model dan import qilamiz
from text_to_json import read_docx_text,parse_test_text,errors


def upload_file(file_path):
    
    # 1. Jadvalni yaratish (agar mavjud bo‘lmasa)
    inspector = inspect(engine)
    if not inspector.has_table("questions"):
        print("ℹ️ Jadval topilmadi. Yaratilmoqda...")
        Base.metadata.create_all(engine)
    else:
        print("📂 Jadval mavjud. Eski ma'lumotlar tozalanmoqda...")

    # --- 2. Session ochamiz ---
    session = SessionLocal()

    # --- 3. Jadval bo‘lsa – ma’lumotlarni o‘chiramiz ---
    if inspector.has_table("questions"):
        session.query(TestQuestion).delete()
        session.commit()

    # --- 4. JSON testlarni olish ---
    quiz = read_docx_text(file_path)
    text_format = parse_test_text(quiz)
    data = text_format

    # --- 5. Har bir savolni DBga yozish ---
    for _, item in data.items():
        question = item['question']
        true = item['true']
        false_variants = [v for k, v in item.items() if k.startswith('false')]
        false_variants += [None] * (4 - len(false_variants))  # to‘ldirish

        row = TestQuestion(
            question=question,
            true=true,
            false_1=false_variants[0],
            false_2=false_variants[1],
            false_3=false_variants[2],
            false_4=false_variants[3]
        )
        session.add(row)

    session.commit()
    session.close()

    return "✅ Barcha savollar muvaffaqiyatli bazaga yozildi."

def all_errors():
    return errors