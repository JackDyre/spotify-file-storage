from main import encode_file
import pyperclip # type: ignore
import tkinter as tk
from tkinter import filedialog

def get_file_path():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askopenfilename()
    


if __name__ == '__main__':
    
    x = None
    while x is None:
        file_path = get_file_path()
        print(file_path)
        x = encode_file(file_path)
    pyperclip.copy(x)
    print('\nHeader playlist ID copied to clipboard')