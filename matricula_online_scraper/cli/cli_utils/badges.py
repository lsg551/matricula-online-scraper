from attr import dataclass
from rich.text import Text
from rich.style import Style
from .color import Color


@dataclass
class Badge:
    Error = Text(
        " ERROR ",
        style=Style(bgcolor=Color.Red, bold=True),
        justify="center",
        end="",
    )

    Warning = Text(
        " WARNING ",
        style=Style(bgcolor=Color.Orange, bold=True),
        justify="center",
        end="",
    )

    Info = Text(
        " INFO ",
        style=Style(bgcolor=Color.Blue, bold=True),
        justify="center",
        end="",
    )

    Success = Text(
        " SUCCESS ",
        style=Style(bgcolor=Color.Green, bold=True),
        justify="center",
        end="",
    )
