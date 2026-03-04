# `__chess__`

> A fully functional two-player terminal chess game, written in Python, with [Pydantic](https://docs.pydantic.dev/latest/) as the data layer and [Textual](https://textual.textualize.io/) / [Rich](rich.readthedocs.io/en/latest/) rendering the board.

<p align="center">
  <img src="dunder-chess.gif"/>
</p>

While researching and writing the [article about Pydantic](https://alanmmolina.com/articles/tools/pydantic), I kept reaching for chess as the cleanest possible domain to demonstrate what the library actually does. Pieces with defined types, positions constrained to a fixed file-and-rank grid, every rule expressible as a validation constraint. The examples wrote themselves. Somewhere along the way I started wondering what would happen if I didn't stop at the examples.

Chess is a surprisingly honest problem for a type-safe data model. Every outcome follows directly from decisions made on a completely visible board, under rules that apply the same way every time. The discipline that makes Pydantic useful, declaring what data must look like and then enforcing it at runtime, maps almost directly onto what a chess engine needs to be correct. So I kept going.

The result is `__chess__` (or `dunder-chess`): a terminal application that enforces the full standard ruleset and runs entirely in your terminal.

## How it works

**Pydantic** is the foundation. The board, each piece, every position, and each recorded move are all Pydantic models. The move engine separates raw _reachability_ from _legality_. One layer generates the squares each piece can physically reach; the other filters those candidates by simulating each move on a scratch board and keeping only the ones that don't leave the moving side's king in check.

The TUI is built with **Textual** and **Rich**. Two panels: the **board** on the left, with cursor, selection, and legal-move highlights all rendered from the current game state on every pass; a **sidebar** on the right showing move history and captured pieces derived directly from the move log.

## Running locally

Clone the repo and launch the game:

```bash
git clone https://github.com/alanmmolina/dunder-chess
cd dunder-chess
uv run dunder-chess
```

## Controls

| Key | Action |
|---|---|
| `↑` `↓` `←` `→` | Move cursor |
| `Enter` / `Space` | Select piece / confirm move |
| `Escape` | Deselect |
| `r` | Restart |
| `q` | Quit |

On the **first `Enter`**, the piece under the cursor is selected and all legal destinations are highlighted. On the **second `Enter`**, the move is executed. If the cursor is on a different friendly piece that has legal moves, the selection switches to that piece instead of treating it as an error. Illegal destinations are silently rejected and the cursor stays in place.

## Rules implemented

The engine enforces all standard piece movements for all six piece types, including diagonal-only captures for pawns. Captures are recorded in move history and the sidebar reflects them in real time. **Check detection** blocks any move that would leave the moving side's king in check. **Checkmate** and **stalemate** are both detected by exhausting the full legal-move set for the current player after each turn.

## Project structure

```
source/
└── dunder_chess/
    ├── core/
    │   ├── rules.py        # raw move and attack generation per piece type
    │   └── player.py       # check-safe move filtering and game status evaluation
    ├── models/
    │   ├── board.py        # Board — validated Position → Piece mapping
    │   ├── game.py         # Game and GameStatus — full game snapshot per turn
    │   ├── move.py         # Move — piece, from/to positions, captured piece
    │   ├── piece.py        # Piece, PieceType, and Color with unicode symbols
    │   └── position.py     # Position — file/rank validation and algebraic notation
    ├── ui/
    │   └── tui.py          # ChessApp (Textual) with BoardWidget and move history sidebar
    └── main.py             # Typer entry point
tests/
├── core/               # engine unit tests
├── models/             # model unit tests
└── ui/                 # TUI integration tests
```

## Development

```bash
uv run task test      # run the full test suite
uv run task lint      # ruff check
uv run task format    # ruff format
uv run task check     # lint + format check
uv run task fix       # autofix lint + format
```
