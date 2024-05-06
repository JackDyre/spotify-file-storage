import json

with open('13bit_indentifiers.json', 'r') as f:
    x = json.load(f)


seen = []
for i in x:
    if i in seen:
        print(i)
    else:
        seen.append(i)