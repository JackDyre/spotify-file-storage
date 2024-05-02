import os

def directory_info(directory_path):
    # Get list of all items (files and folders) in directory
    all_items = os.listdir(directory_path)

    # Get list of files in directory
    files = [item for item in all_items if os.path.isfile(os.path.join(directory_path, item))]

    # Get list of folders in directory
    folders = [folder for folder in all_items if os.path.isdir(os.path.join(directory_path, folder))]

    # Check if it's possible to zoom out one directory level
    is_parent_directory = os.path.abspath(directory_path) != os.path.abspath(os.sep)

    # Create the dictionary
    directory_dict = {
        "is_parent_directory": is_parent_directory,
        "folders": folders,
        "files": files,
    }

    return directory_dict
