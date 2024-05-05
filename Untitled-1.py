with open('new-id-list.txt', 'r') as f:
    large = eval(f.read())


with open('8194-ids.txt', 'r') as f:
    small = eval(f.read())

for i in range(len(small)):
    if not small[i] == large[i]:
        print(i)
        large[i] = small[i]


with open('new-id-list.txt', 'w') as f:
    f.write(str(large))