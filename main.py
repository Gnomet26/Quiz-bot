from generate import Generate

g = Generate(5)

print("🎲 Random savollar:")
for q in g.new_question():
    print(f"{q['number']}) {q['question']}")
    for i, v in enumerate(q['variants']):
        print(f"  {chr(97+i)}) {v}")

print("\n✅ To‘g‘ri variant indekslari:")
print(g.true_list())
