import gzip as gz

filename = 'id-getter.py'

with open(f'{filename}', 'rb') as file:
    with gz.open(f'__pycache__/{filename}.gz', 'wb') as archive:
        archive.writelines(file)

with gz.open(f'__pycache__/{filename}.gz', 'rb') as archive:
    with open(f'__pycache__/{filename}', 'wb') as file:
        file.write(archive.read())