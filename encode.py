from main import encode_file
import pyperclip # type: ignore

if __name__ == '__main__':
    file_path = input('Paste file path: \n\n')
    x = encode_file(file_path)
    pyperclip.copy(x)
    print('Header playlist ID copied to clipboard')