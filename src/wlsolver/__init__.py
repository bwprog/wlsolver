"""Application Initialization."""
from . import __main__


# ~~~ #     - allow typer app in __main__.py to be executed from __init__.py -
def main() -> None:
    """For the [project.scripts] section of pyproject.toml execution by uv (e.g. 'uv run wlsolver <board>')."""
    __main__.app()
