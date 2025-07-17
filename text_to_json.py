import json
import re
from docx import Document

errors = []

def read_docx_text(file_path):
    doc = Document(file_path)
    full_text = '\n'.join([para.text for para in doc.paragraphs])
    return full_text

def parse_test_text(text):
    raw_questions = re.findall(r'(\d+)\)(.*?)((?=\n\s*\d+\))|$)', text, flags=re.DOTALL)
    result = {}

    for match in raw_questions:
        question_id = match[0].strip()
        question_block = match[1].strip()

        parts = re.split(r'(?=\s*a\))', question_block, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) < 2:
            errors.append(f"⚠️  Savol {question_id} o'tkazildi: variantlar topilmadi.")
            continue

        question_text = parts[0].strip().replace('\n', ' ')
        options_text = parts[1]

        options = re.findall(r'[a-d]\)\s*([^\n\r]+?)(?=(?:\s+[a-d]\))|$)', options_text, flags=re.IGNORECASE)

        if len(options) < 2:
            errors.append(f"⚠️  Savol {question_id} o'tkazildi: variantlar soni yetarli emas. ({len(options)} ta topildi)")
            continue

        question_data = {
            "question": question_text,
            "true": options[0].strip()
        }

        for i, opt in enumerate(options[1:], start=1):
            question_data[f"false_{i}"] = opt.strip()

        result[question_id] = question_data

    return result

# === FOYDALANISH ===
'''file_path = 'data.docx'  # ← Word faylingiz nomi shu yerda
doc_text = read_docx_text(file_path)
parsed_json = parse_test_text(doc_text)


# JSON natijani chiqarish
print("\n📦 JSON ko'rinishi:")
print(json.dumps(parsed_json, indent=4, ensure_ascii=False))'''
