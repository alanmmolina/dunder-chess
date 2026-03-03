from typing import ClassVar

from rich.console import Group, RenderableType
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Footer, Label, Rule, Static

from ..core.player import apply_move, evaluate_moves
from ..models.game import Game, GameStatus
from ..models.piece import Color
from ..models.position import Position
from ..utils.constants import FILES

_PINK = "#E92063"  # Pydantic brand pink — cursor
_PINK_DIM = "#8b103a"  # darker pink — legal-move hints
_PINK_MID = "#c41d57"  # mid pink — selected piece
_LEGAL = _PINK_DIM  # legal-move hints

_LIGHT = "#d4d4d8"  # light board squares (zinc-300)
_DARK = "#1e1e24"  # dark board squares (near-black)
_CHECK = "#ff1744"  # king-in-check square

_FG_LIGHT = "#1a0010"  # text on light squares
_FG_DARK = "#f9e0e8"  # text on dark squares


class BoardWidget(Widget):
    """Interactive 8x8 chess board widget."""

    can_focus = True

    BINDINGS: ClassVar[list] = [
        Binding("up", "cursor_up", "Navigate", show=True),
        Binding("down", "cursor_down", "", show=False),
        Binding("left", "cursor_left", "", show=False),
        Binding("right", "cursor_right", "", show=False),
        Binding("enter", "confirm", "Select / Move", show=True),
        Binding("space", "confirm", "", show=False),
        Binding("escape", "deselect", "Deselect", show=True),
    ]

    DEFAULT_CSS = """
    BoardWidget {
        width: 51;
        height: 25;
    }
    """

    def __init__(self) -> None:
        """Initialise game state, cursor position, and selection bookkeeping."""
        super().__init__()
        self._state: Game = Game.initial()
        self._cursor_file: int = 4
        self._cursor_rank: int = 1
        self._selected: Position | None = None
        self._legal_targets: set[str] = set()
        self._message: str = ""

    def render(self) -> RenderableType:
        """Render the board as a Rich Group of Text rows."""
        return self._build_board()

    def _cursor_notation(self) -> str:
        """Return the algebraic notation of the square currently under the cursor."""
        return f"{FILES[self._cursor_file]}{self._cursor_rank + 1}"

    def _square_bg(self, file_idx: int, rank_idx: int, notation: str) -> str:
        """
        Choose a background color for a single board square.

        Priority order (highest first):
        1. Cursor position — bright pink.
        2. Selected piece — mid pink.
        3. Legal-move hint — dim pink.
        4. King-in-check square — red.
        5. Natural square color — light or dark based on file/rank parity.
        """
        king_check_notation = ""
        if self._state.status == GameStatus.CHECK:
            king_check_notation = self._state.board.king_position(self._state.turn).notation

        if notation == self._cursor_notation():
            return _PINK
        if self._selected and notation == self._selected.notation:
            return _PINK_MID
        if notation in self._legal_targets:
            return _LEGAL
        if notation == king_check_notation:
            return _CHECK

        is_light = (file_idx + rank_idx) % 2 == 0
        return _LIGHT if is_light else _DARK

    def _build_board(self) -> Group:
        """Three Rich Text lines per rank (pad / symbol / pad) for a square board."""
        rows: list[Text] = []

        for rank in range(8, 0, -1):
            rank_idx = rank - 1

            bg_colors: list[str] = []
            fg_colors: list[str] = []
            symbols: list[str] = []
            for file_idx, file in enumerate(FILES):
                notation = f"{file}{rank}"
                piece = self._state.board.get(Position.from_notation(notation))
                bg_color = self._square_bg(file_idx, rank_idx, notation)
                is_light = (file_idx + rank_idx) % 2 == 0
                if piece:
                    if piece.color == Color.WHITE:
                        fg_color = "bright_white"
                    else:
                        fg_color = _FG_LIGHT if is_light else _FG_DARK
                    symbol = piece.symbol
                else:
                    fg_color = _FG_LIGHT if is_light else _FG_DARK
                    symbol = " "
                bg_colors.append(bg_color)
                fg_colors.append(fg_color)
                symbols.append(symbol)

            top = Text(no_wrap=True)
            top.append("   ")
            for bg_color in bg_colors:
                top.append("      ", style=f"on {bg_color}")
            rows.append(top)

            mid = Text(no_wrap=True)
            mid.append(f" {rank} ", style=f"bold {_PINK}")
            for col_idx in range(8):
                style = f"bold {fg_colors[col_idx]} on {bg_colors[col_idx]}"
                mid.append(f"  {symbols[col_idx]}   ", style=style)
            rows.append(mid)

            bot = Text(no_wrap=True)
            bot.append("   ")
            for bg_color in bg_colors:
                bot.append("      ", style=f"on {bg_color}")
            rows.append(bot)

        file_row = Text(no_wrap=True)
        file_row.append("   ")
        for file in FILES:
            file_row.append(f"  {file}   ", style=f"bold {_PINK}")
        rows.append(file_row)

        return Group(*rows)

    def _guard(self) -> bool:
        """Return True if the game is over (actions should be ignored)."""
        return self._state.status in (GameStatus.CHECKMATE, GameStatus.STALEMATE)

    def action_cursor_up(self) -> None:
        """Move the cursor one rank up (towards rank 8)."""
        if not self._guard():
            self._cursor_rank = min(7, self._cursor_rank + 1)
            self._refresh_ui()

    def action_cursor_down(self) -> None:
        """Move the cursor one rank down (towards rank 1)."""
        if not self._guard():
            self._cursor_rank = max(0, self._cursor_rank - 1)
            self._refresh_ui()

    def action_cursor_left(self) -> None:
        """Move the cursor one file to the left (towards the a-file)."""
        if not self._guard():
            self._cursor_file = max(0, self._cursor_file - 1)
            self._refresh_ui()

    def action_cursor_right(self) -> None:
        """Move the cursor one file to the right (towards the h-file)."""
        if not self._guard():
            self._cursor_file = min(7, self._cursor_file + 1)
            self._refresh_ui()

    def action_confirm(self) -> None:
        """Handle Enter/Space: select a piece on the first press, attempt a move on the second."""
        if not self._guard():
            self._handle_confirm()
            self._refresh_ui()

    def action_deselect(self) -> None:
        """Clear the current selection and legal-move highlights on Escape."""
        if not self._guard():
            self._deselect()
            self._refresh_ui()

    def _handle_confirm(self) -> None:
        """Select a piece if none is selected; otherwise attempt to move the selected piece."""
        notation = self._cursor_notation()
        if self._selected is None:
            self._try_select(notation)
        else:
            self._try_move(notation)

    def _try_select(self, notation: str) -> None:
        """
        Attempt to select the piece on notation as the piece to move.

        Validates that the square holds a friendly piece with at least one
        legal destination.  Sets the selection and highlights legal targets
        on success; writes an error message otherwise.
        """
        position = Position.from_notation(notation)
        piece = self._state.board.get(position)
        if piece is None or piece.color != self._state.turn:
            self._message = "Select one of your pieces first."
            return
        legal_destinations = evaluate_moves(position, self._state)
        if not legal_destinations:
            self._message = "That piece has no legal moves."
            return
        self._selected = position
        self._legal_targets = {destination.notation for destination in legal_destinations}
        self._message = "Move cursor to a pink square, then Enter."

    def _try_move(self, notation: str) -> None:
        """
        Attempt to move the currently selected piece to notation.

        If the destination holds another friendly piece with legal moves, the
        selection switches to that piece instead.  If the destination is not in
        the legal-move set, an error is shown.  On a valid move the game state
        is advanced and the selection is cleared.
        """
        destination = Position.from_notation(notation)
        piece = self._state.board.get(destination)
        if piece is not None and piece.color == self._state.turn:
            legal_destinations = evaluate_moves(destination, self._state)
            if legal_destinations:
                self._selected = destination
                self._legal_targets = {p.notation for p in legal_destinations}
                self._message = "Move cursor to a pink square, then Enter."
                return

        if notation not in self._legal_targets:
            self._message = "Not a legal move. Esc to cancel."
            return

        assert self._selected is not None
        new_state = apply_move(
            self._selected,
            destination,
            self._state,
        )
        if new_state is None:
            self._message = "Illegal move."
            self._deselect()
            return

        self._state = new_state
        self._deselect()

    def _deselect(self) -> None:
        """Clear the selected piece, legal-move highlights, and status message."""
        self._selected = None
        self._legal_targets = set()
        self._message = ""

    def _refresh_ui(self) -> None:
        """Repaint the board widget and update all sidebar labels."""
        self.refresh()
        app = self.app
        app.query_one("#status", Label).update(self._status_markup())
        app.query_one("#history", Label).update(self._history_markup())
        app.query_one("#captured", Label).update(self._captured_markup())

    def _status_markup(self) -> str:
        """Return Rich markup describing the current game status."""
        status = self._state.status
        turn = "♔ White" if self._state.turn == Color.WHITE else "♚ Black"

        if status == GameStatus.CHECKMATE:
            winner = "♚ Black" if self._state.turn == Color.WHITE else "♔ White"
            return (
                f"[{_PINK} bold]Checkmate! {winner} wins![/]"
                f"\n[dim]Press [bold]r[/bold] to play again[/dim]"
            )
        if status == GameStatus.STALEMATE:
            return (
                f"[{_PINK} bold]Stalemate — draw.[/]\n[dim]Press [bold]r[/bold] to play again[/dim]"
            )
        if status == GameStatus.CHECK:
            line1 = f"[bold red]✕  {turn} is in check![/bold red]"
        else:
            line1 = f"[bold white]{turn}[/bold white] [dim]to move[/dim]"

        return line1

    def _history_markup(self) -> str:
        """
        Return Rich markup with a two-column move-history table.

        White moves are shown in the left column, Black in the right.  At most
        the last fourteen half-moves (seven full moves) are displayed to keep
        the sidebar a fixed height.
        """
        history = self._state.history
        column_width = 12
        header = f"    [bold white]♔ {'White':<{column_width - 2}}[/bold white][bold]♚ Black[/bold]"
        if not history:
            return header + "\n[dim]—[/dim]"
        move_lines: list[str] = []
        for pair_idx in range(0, len(history), 2):
            move_num = pair_idx // 2 + 1
            white_notation = history[pair_idx].notation
            has_black = pair_idx + 1 < len(history)
            black_notation = history[pair_idx + 1].notation if has_black else ""
            move_lines.append(
                f"[dim]{move_num:>3}.[/dim] "
                f"[white]{white_notation:<{column_width}}[/white]"
                f"[dim]{black_notation}[/dim]"
            )
        return header + "\n" + "\n".join(move_lines[-14:])

    def _captured_markup(self) -> str:
        """Return Rich markup listing pieces captured by each side, shown as Unicode symbols."""
        lost_by_white: list[str] = []
        lost_by_black: list[str] = []
        for move in self._state.history:
            if move.captured_piece is not None:
                if move.captured_piece.color == Color.WHITE:
                    lost_by_white.append(move.captured_piece.symbol)
                else:
                    lost_by_black.append(move.captured_piece.symbol)
        white_display = "".join(lost_by_black) if lost_by_black else "[dim]—[/dim]"
        black_display = "".join(lost_by_white) if lost_by_white else "[dim]—[/dim]"
        return (
            f"[bold white]♔ White:[/bold white] {white_display}\n"
            f"[bold]♚ Black:[/bold] {black_display}"
        )

    def restart(self) -> None:
        """Reset the board to the initial position and clear all cursor and selection state."""
        self._state = Game.initial()
        self._cursor_file = 4
        self._cursor_rank = 1
        self._deselect()
        self._refresh_ui()


class ChessApp(App[None]):

    TITLE = "__chess__.py"

    CSS = f"""
    Screen {{
        background: #09090b;
    }}

    #app-header {{
        layout: horizontal;
        height: 1;
        background: #09090b;
        padding: 0 1;
    }}

    #header-title {{
        width: 1fr;
        color: {_PINK};
        text-style: bold;
    }}

    #header-user {{
        width: auto;
        color: white;
    }}

    #main {{
        height: 1fr;
        layout: horizontal;
    }}

    #board-panel {{
        width: 1fr;
        height: 1fr;
        align: center middle;
        layout: vertical;
    }}

    BoardWidget {{
        width: 51;
        height: 25;
    }}

    #status {{
        width: 51;
        height: auto;
        margin-top: 1;
        color: white;
    }}

    #sidebar {{
        width: 34;
        height: 1fr;
        border-left: solid {_PINK};
        padding: 1 2;
        layout: vertical;
    }}

    #sidebar-title {{
        color: {_PINK};
        text-style: bold;
    }}

    Rule {{
        color: {_PINK};
        margin: 0;
    }}
    #history {{
        color: #a1a1aa;
        height: 1fr;
        margin-top: 1;
    }}

    #captured {{
        color: #a1a1aa;
        height: auto;
        margin-top: 1;
    }}

    Footer {{
        background: #09090b;
        color: {_PINK};
    }}
    """

    BINDINGS: ClassVar[list] = [
        Binding("q", "quit", "Quit", show=True),
        Binding("r", "restart", "Restart", show=True),
    ]

    def compose(self) -> ComposeResult:
        """Build the widget tree: header bar, board panel, move-history sidebar, and footer."""
        with Static(id="app-header"):
            yield Label("__chess__.py", id="header-title")
            yield Label("~/.alanmmolina", id="header-user")
        with Static(id="main"):
            with Static(id="board-panel"):
                yield BoardWidget()
                yield Label("", id="status")
            with Static(id="sidebar"):
                yield Label("Move History", id="sidebar-title")
                yield Rule()
                yield Label("[dim]No moves yet.[/dim]", id="history")
                yield Rule()
                yield Label("", id="captured")
        yield Footer()

    def on_mount(self) -> None:
        """Focus the board widget and trigger an initial UI refresh after the app mounts."""
        board = self.query_one(BoardWidget)
        board.focus()
        board._refresh_ui()

    def action_restart(self) -> None:
        """Delegate a game restart to the BoardWidget."""
        self.query_one(BoardWidget).restart()


def run() -> None:
    """Launch the Textual chess TUI."""
    ChessApp().run()
