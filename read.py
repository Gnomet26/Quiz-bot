import random
import json
from db import SessionLocal
from test_model import TestQuestion

def generate_random_questions():
    session = SessionLocal()
    questions = session.query(TestQuestion).all()
    total = len(questions)

    selected = random.sample(questions, total)
    result = {}

    for i, q in enumerate(selected, 1):
        # To'g'ri va noto'g'ri variantlar
        options = [q.true]
        false_variants = [q.false_1, q.false_2, q.false_3, q.false_4]
        options += [f for f in false_variants if f]  # None bo'lmaganlar

        # Har doim a) variant to'g'ri deb qabul qilinadi
        item = {
            "question": q.question,
        }

        # Tasodifiy aralashtirilmagan holda: a) = true
        item["true"] = q.true
        for f in options[1:]:
            item.setdefault("false", []).append(f)

        # False larni to'g'ri formatda JSONga ajratish
        result[str(i)] = {
            "question": item["question"],
            "true": item["true"],
        }

        # false qiymatlarni "false" kalitida takror yozamiz
        for idx, fval in enumerate(item.get("false", []), 1):
            result[str(i)][f"false{idx}"] = fval

    return result

def get_all_questions():
    return generate_random_questions()
