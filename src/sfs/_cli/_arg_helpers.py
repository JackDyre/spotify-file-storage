"""Abstraction functions for adding arg to argument parsers."""
import argparse
from pathlib import Path


def _add_key_arg(parser: argparse.ArgumentParser, help_msg: str) -> None:
    parser.add_argument("key", type=str, help=help_msg)


def _add_path_arg(
    parser: argparse.ArgumentParser, path_type: str, help_msg: str
) -> None:
    is_path_type = {"file": Path.is_file, "dir": Path.is_dir}[path_type]
    parser.add_argument(
        f"{path_type}-path",
        type=lambda p: Path(p)
        if is_path_type(Path(p))
        else (_ for _ in ()).throw(
            argparse.ArgumentTypeError(f"{p} is not a {path_type}")
        ),
        help=help_msg,
    )


def _add_id_opt(parser: argparse.ArgumentParser, help_msg: str) -> None:
    parser.add_argument("-i", "--id", type=str, help=help_msg)
