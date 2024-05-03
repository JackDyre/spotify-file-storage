import sqlite3


def decimal_to_binary_padded(decimal, pad):
    binary = ""
    while decimal > 0:
        remainder = decimal % 2
        binary = str(remainder) + binary
        decimal = decimal // 2
    binary = binary.zfill(pad)
    return [int(bit) for bit in binary]



conn = sqlite3.connect('pad_13_lookup.db')

cursor = conn.cursor()


# binary = [decimal_to_binary_padded(i, 13) for i in range(8192)] + [0, 1]
# with open('8194-ids.txt', 'r') as f:
#     track_ids = eval(f.read())

# cursor.execute('''CREATE TABLE IF NOT EXISTS pad13_id_lookup (
#                     binary TEXT PRIMARY KEY,
#                     track_id TEXT
#                 )''')


# for i in range(8194):
#     cursor.execute("INSERT INTO pad13_id_lookup (binary, track_id) VALUES (?, ?)", (str(binary[i]), track_ids[i]))

# conn.commit()

# cursor.execute("SELECT * FROM pad13_id_lookup")
# rows = cursor.fetchall()
# for row in rows:
#     print(row)


cursor.execute("SELECT * FROM pad13_id_lookup WHERE binary = ?", (str(decimal_to_binary_padded(6000,13)),))
track_id = cursor.fetchall()
print(track_id[0])

cursor.close()
conn.close()