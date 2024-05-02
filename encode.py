from main import encode_file
import pyperclip # type: ignore
import os
from directory_info import directory_info

def get_file_path(dir_input = None):
    directory = dir_input or os.getcwd()
    dir_dict = directory_info(directory)
    options = {}
    print(f'\nCurrent Directory: {directory}')
    for key in dir_dict:
        if key == 'folders':
            if len(dir_dict[key]):
                print('\nFolders:')
                for idx, item in enumerate(dir_dict[key], start=1):
                    print(f'>{idx}: {item}')
                    options[f'>{idx}'] = os.path.join(directory, item)
                print('\n')
        elif key == 'files':
                if len(dir_dict[key]):
                    print('\nFiles:')
                    for idx, item in enumerate(dir_dict[key], start=1):
                        print(f'-{idx}: {item}')
                        options[f'-{idx}'] = [item]
                    print('\n')
        else:
             if dir_dict[key] == True:
                  print('\nParent Directory:\n<: Parent Directory\n')
                  options['<'] = os.path.dirname(directory)
    
    selected_option = input('Input choice: ')
    if type(options[selected_option]) is list:
        return os.path.join(directory, options[selected_option][0])
    else:
        recursive = get_file_path(dir_input=options[selected_option])
        return recursive


if __name__ == '__main__':
    
    x = None
    while x is None:
        file_path = get_file_path()
        print(file_path)
        x = encode_file(file_path)
    pyperclip.copy(x)
    print('\nHeader playlist ID copied to clipboard')