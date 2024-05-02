from main import decode_file

if __name__ == '__main__':
    header_playlist = input('Paste header playlist URL/ID:\n\n')
    file = decode_file(header_playlist)
    print(f'File successfully decoded and saved as {file}')