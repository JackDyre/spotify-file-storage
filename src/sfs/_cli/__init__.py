"""Private submodule for parsing command line args."""

import argparse

from ._subcommand_parsers import (
    _parse_download_subcommand,
    _parse_remove_subcommand,
    _parse_upload_subcommand,
    _parse_vfs_subcommand,
)


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="sfs", description="A proof of concept file storage CLI tool"
    )

    subparsers = parser.add_subparsers(
        title="subcommands", dest="subcommand", required=True
    )

    _parse_upload_subcommand(subparsers)
    _parse_download_subcommand(subparsers)
    _parse_remove_subcommand(subparsers)
    _parse_vfs_subcommand(subparsers)

    return parser.parse_args()


PARSED_ARGS = _parse_arguments()
