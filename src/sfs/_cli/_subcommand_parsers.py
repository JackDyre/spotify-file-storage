"""Parsers for each of the 4 subcommands."""

import argparse

from ._arg_helpers import _add_id_opt, _add_key_arg, _add_path_arg
from ._vfs_subcommand_parsers import (
    _parse_vfs_connect_subcommand,
    _parse_vfs_new_subcommand,
)


def _parse_upload_subcommand(subparsers: argparse._SubParsersAction) -> None:
    upload_parser = subparsers.add_parser(
        "upload",
        help="Upload a file to Spotify playlist(s)",
    )

    _add_key_arg(upload_parser, "Secret key for encrypting the file")

    _add_path_arg(upload_parser, "file", "Path to the file to upload")


def _parse_download_subcommand(subparsers: argparse._SubParsersAction) -> None:
    download_parser = subparsers.add_parser(
        "download", help="Download a file from Spotify playlist(s)"
    )

    _add_key_arg(download_parser, "Secret key for decrypting the file")

    _add_path_arg(
        download_parser, "dir", "Path to the directory to download the file into"
    )

    _add_id_opt(download_parser, "The ID of the head playlist of the file")


def _parse_remove_subcommand(subparsers: argparse._SubParsersAction) -> None:
    remove_parser = subparsers.add_parser(
        "remove", help="Remove a single file from Spotify"
    )

    _add_key_arg(remove_parser, "Secret key for decrypting the file")

    _add_id_opt(remove_parser, "The ID of the head playlist of the file")


def _parse_vfs_subcommand(subparsers: argparse._SubParsersAction) -> None:
    vfs_parser = subparsers.add_parser(
        "vfs", help="Virtual File System using Spotify playlists"
    )

    vfs_subparsers = vfs_parser.add_subparsers(
        title="subcommands", dest="subcommand", required=True
    )

    _parse_vfs_connect_subcommand(vfs_subparsers)
    _parse_vfs_new_subcommand(vfs_subparsers)
