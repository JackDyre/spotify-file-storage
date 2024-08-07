"""Parsers for each of the 4 subcommands."""
import argparse
from pathlib import Path

from ._vfs_subcommand_parsers import (
    _parse_vfs_connect_subcommand,
    _parse_vfs_new_subcommand,
)


def _parse_upload_subcommand(subparsers: argparse._SubParsersAction) -> None:
    upload_parser = subparsers.add_parser(
        "upload",
        help="Upload a file to Spotify playlist(s)",
    )

    upload_parser.add_argument(
        "key",
        type=str,
        help="Secret key for encrypting the file. Must be unique",
    )

    upload_parser.add_argument(
        "filepath",
        type=lambda p: Path(p)
        if Path(p).is_file()
        else (_ for _ in ()).throw(argparse.ArgumentTypeError(f"{p} is not a file")),
        help="Path to the file to upload",
    )


def _parse_download_subcommand(subparsers: argparse._SubParsersAction) -> None:
    download_parser = subparsers.add_parser(
        "download", help="Download a file from Spotify playlist(s)"
    )

    download_parser.add_argument(
        "key",
        type=str,
        help="Secret key for decrypting the file",
    )

    download_parser.add_argument(
        "filepath",
        type=lambda p: Path(p)
        if Path(p).is_dir()
        else (_ for _ in ()).throw(
            argparse.ArgumentTypeError(f"{p} is not a directory")
        ),
        help="Path to the directory to download the file into",
    )

    download_parser.add_argument(
        "-i", "--id", type=str, help="The ID of the head playlist of the file"
    )


def _parse_remove_subcommand(subparsers: argparse._SubParsersAction) -> None:
    remove_parser = subparsers.add_parser(
        "remove", help="Remove a single file from Spotify"
    )

    remove_parser.add_argument(
        "key",
        type=str,
        help="Secret key for decrypting the file",
    )

    remove_parser.add_argument(
        "-i", "--id", type=str, help="The ID of the head playlist of the file"
    )


def _parse_vfs_subcommand(subparsers: argparse._SubParsersAction) -> None:
    vfs_parser = subparsers.add_parser(
        "vfs", help="Virtual File System using Spotify playlists"
    )

    vfs_subparsers = vfs_parser.add_subparsers(
        title="subcommands", dest="subcommand", required=True
    )

    _parse_vfs_connect_subcommand(vfs_subparsers)
    _parse_vfs_new_subcommand(vfs_subparsers)
