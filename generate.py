# generate.py
import random
from read import get_all_questions

class Generate:
    def __init__(self, amount: int):
        all_qs = list(get_all_questions().values())
        if amount > len(all_qs):
            raise ValueError("So‘ralgan savollar soni mavjudidan katta!")

        self.selected = random.sample(all_qs, amount)
        self.result = []
        self.true_index_map = {}

    def new_question(self):
        output = []

        for i, item in enumerate(self.selected, 1):
            q_text = item['question']
            true_answer = item['true']

            all_variants = [true_answer]
            for key in ['false1', 'false2', 'false3', 'false4']:
                val = item.get(key)
                if val:
                    all_variants.append(val)

            random.shuffle(all_variants)

            self.true_index_map[str(i)] = str(all_variants.index(true_answer))

            output.append({
                "number": i,
                "question": q_text,
                "variants": all_variants
            })

        self.result = output
        return output

    def true_list(self):
        return self.true_index_map