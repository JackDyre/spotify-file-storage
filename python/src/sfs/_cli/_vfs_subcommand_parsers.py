"""Parsers for the 2 subcommands of the vfs subcommand."""

import argparse

from ._arg_helpers import _add_id_opt, _add_key_arg


def _parse_vfs_new_subcommand(subparsers: argparse._SubParsersAction) -> None:
    new_parser = subparsers.add_parser("new", help="Create a new VFS")

    _add_key_arg(new_parser, "Secret key for encrypting the VFS")


def _parse_vfs_connect_subcommand(subparsers: argparse._SubParsersAction) -> None:
    connect_parser = subparsers.add_parser("connect", help="Connect to a VFS")

    _add_key_arg(connect_parser, "Secret key for decrypting the VFS")

    _add_id_opt(connect_parser, "The ID of the head playlist of the VFS")
