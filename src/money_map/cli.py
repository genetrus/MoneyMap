"""MoneyMap CLI scaffold."""

import typer

app = typer.Typer(help="MoneyMap CLI (scaffold).")


def _not_implemented(action: str) -> None:
    typer.echo(f"{action} is not implemented yet.")


@app.command()
def validate() -> None:
    """Validate datasets and rules."""
    _not_implemented("validate")


@app.command()
def recommend() -> None:
    """Recommend top variants."""
    _not_implemented("recommend")


@app.command()
def plan() -> None:
    """Generate a route plan for a selected variant."""
    _not_implemented("plan")


@app.command()
def export() -> None:
    """Export plan artifacts."""
    _not_implemented("export")


@app.command()
def ui() -> None:
    """Launch the UI."""
    typer.echo("UI not implemented yet. Add a UI runner when available.")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
