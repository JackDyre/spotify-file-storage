"""
(serial_read_write.py) Uses pythons pickle module to read and write to and
from serialized files
"""

import pickle
from os.path import dirname, realpath
from typing import Any


class SerializeFile:
    """
    A utility class for reading from and writing to serialized files using Python's pickle module.

    Attributes:
        - self.name (str): The name of the file.
        - self.directory (str): The directory path where the file is located.
        - self.extension (str): The file extension, defaults to ".pickle".
        - self.full_path (str): The complete path of the file including
            directory and extension.
    """

    def __init__(
        self,
        file_name: str,
        file_directory: str | None = None,
        file_extension: str = ".pickle",
    ) -> None:

        self.name = file_name
        self.directory = file_directory or dirname(realpath(__file__))
        self.extension = file_extension
        self.full_path = f"{self.directory}\\{self.name}{self.extension}"

    @property
    def read(self) -> Any:
        """
        (Property) Reads the serial file using the Pickle module and
        returns whatever object was 'pickled'.

        Returns (Any):
            - Whatever object was 'pickled' or a string
                containing an error message.
        """
        try:
            with open(self.full_path, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError as e:
            return self.file_not_found(e)

    def write(self, obj: Any) -> None | str:
        """
        'Pickles' an object to a serialized binary file.

        Returns (None | str):
            - None if the object is successfully 'pickled'
            - str containing error message if unsuccessful
        """
        try:
            with open(self.full_path, "wb") as f:
                pickle.dump(obj, f)
            return None
        except FileNotFoundError as e:
            return self.file_not_found(e)

    def file_not_found(self, e):
        """
        Gives the error error message if self.read or self.write is unsuccessful

        Returns (str):
            - str containing error message
        """
        return f"!! [ERROR] !! : Unable to locate file/path: {e}"


def init_serialized_file(
    file_name: str, file_directory: str | None = None, file_extension: str = ".pickle"
) -> SerializeFile:
    """
    Creates an instance of the SerializeFile class for use in
    reading and writing to serialized binary files.

    Returns (SerializeFile):
        - An instance of the SerializedFile class
    """
    return SerializeFile(
        file_name=file_name,
        file_directory=file_directory,
        file_extension=file_extension,
    )
