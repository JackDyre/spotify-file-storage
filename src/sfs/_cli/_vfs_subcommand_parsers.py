"""Parsers for the 2 subcommands of the vfs subcommand."""
import argparse


def _parse_vfs_new_subcommand(subparsers: argparse._SubParsersAction) -> None:
    new_parser = subparsers.add_parser("new", help="Create a new VFS")

    new_parser.add_argument(
        "key",
        type=str,
        help="Secret key for encrypting the VFS",
    )


def _parse_vfs_connect_subcommand(subparsers: argparse._SubParsersAction) -> None:
    connect_parser = subparsers.add_parser("connect", help="Connect to a VFS")

    connect_parser.add_argument(
        "key",
        type=str,
        help="Secret key for decrypting the VFS",
    )

    connect_parser.add_argument(
        "-i", "--id", type=str, help="The ID of the head playlist of the VFS"
    )
