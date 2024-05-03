import tkinter as tk
from tkinter import filedialog

def open_file_dialog():
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    file_path = filedialog.askopenfilename()  # Open file dialog and get selected file path

    if file_path:
        print("Selected file:", file_path)
    else:
        print("No file selected.")

if __name__ == "__main__":
    open_file_dialog()
