"""Shorten a path to a more user-friendly format."""

from pathlib import Path


def shorten_path(path: Path) -> str:
    """Shortens a given path to a more user-friendly format.

    Examples:
        >>> shorten_path(Path("/home/user/documents/file.txt"))
        '~/documents/file.txt'

    Args:
        path (Path): The path to be shortened.

    Returns:
        str: Shortend path as string.
    """
    home = Path.home()
    cwd = Path.cwd()
    path = path.resolve()

    if path == cwd:
        short = "."
    elif cwd in path.parents:
        short = f"./{path.relative_to(cwd)}"
    elif home in path.parents:
        short = f"~/{path.relative_to(home)}"
    else:
        short = str(path)

    return short
