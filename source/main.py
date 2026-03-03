import typer

from .ui.tui import run

app = typer.Typer(name="dunder-chess", help="Two-player terminal chess game.")


@app.command()
def play() -> None:
    """Start a two-player chess game."""
    run()


if __name__ == "__main__":
    app()
