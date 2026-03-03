import asyncio

from dunder_chess.models.board import Board
from dunder_chess.models.game import Game, GameStatus
from dunder_chess.models.piece import Color, Piece, PieceType
from dunder_chess.models.position import Position
from dunder_chess.ui.tui import BoardWidget, ChessApp


def _pos(notation: str) -> Position:
    return Position.from_notation(notation)


def _piece(piece_type: PieceType, color: Color = Color.WHITE) -> Piece:
    return Piece(type=piece_type, color=color)


def _widget() -> BoardWidget:
    """Return a freshly constructed BoardWidget outside of a running app."""
    return BoardWidget()


def _game_with_status(status: GameStatus) -> Game:
    """Return an initial board with the given status forced in."""
    return Game(
        board=Game.initial().board,
        turn=Color.WHITE,
        history=[],
        status=status,
    )


def test_cursor_notation_initial():
    """Cursor starts at e2 (file_index=4, rank_index=1 → rank 2)."""
    assert _widget()._cursor_notation() == "e2"


def test_cursor_notation_at_a1():
    """file=0, rank=0 → a1."""
    widget = _widget()
    widget._cursor_file = 0
    widget._cursor_rank = 0
    assert widget._cursor_notation() == "a1"


def test_cursor_notation_at_h8():
    """file=7, rank=7 → h8."""
    widget = _widget()
    widget._cursor_file = 7
    widget._cursor_rank = 7
    assert widget._cursor_notation() == "h8"


def test_guard_false_when_active():
    """Active game: guard returns False — moves are permitted."""
    assert _widget()._guard() is False


def test_guard_true_when_checkmate(fools_mate_state):
    """Checkmate: guard returns True — no further input should be processed."""
    widget = _widget()
    widget._state = fools_mate_state
    assert widget._guard() is True


def test_guard_true_when_stalemate():
    """Stalemate: guard returns True — no further input should be processed."""
    widget = _widget()
    widget._state = _game_with_status(GameStatus.STALEMATE)
    assert widget._guard() is True


def test_try_select_own_piece_records_selection():
    """Selecting a white pawn on e2 stores the position and legal targets."""
    widget = _widget()
    widget._try_select("e2")
    assert widget._selected is not None
    assert widget._selected.notation == "e2"
    assert "e3" in widget._legal_targets
    assert "e4" in widget._legal_targets


def test_try_select_opponent_piece_sets_message():
    """Trying to select a black piece on WHITE's turn sets a non-empty message."""
    widget = _widget()
    widget._try_select("e7")
    assert widget._selected is None
    assert widget._message != ""


def test_try_select_empty_square_sets_message():
    """Trying to select an empty square (e4) sets a non-empty message."""
    widget = _widget()
    widget._try_select("e4")
    assert widget._selected is None
    assert widget._message != ""


def test_try_move_legal_advances_state():
    """Moving e2→e4 updates the board, clears selection, and flips the turn."""
    widget = _widget()
    widget._try_select("e2")
    widget._try_move("e4")
    assert widget._selected is None
    assert widget._state.board.get(_pos("e4")) is not None
    assert widget._state.board.get(_pos("e2")) is None
    assert widget._state.turn == Color.BLACK


def test_try_move_illegal_destination_keeps_selection():
    """Moving to a non-legal square sets an error message and preserves the selection."""
    widget = _widget()
    widget._try_select("e2")
    widget._try_move("e5")  # pawn on e2 cannot reach e5 in one move
    assert widget._selected is not None
    assert widget._message != ""


def test_try_move_to_friendly_piece_switches_selection():
    """Moving cursor onto another friendly piece re-selects that piece instead."""
    widget = _widget()
    widget._try_select("d2")  # select d-pawn
    widget._try_move("e2")  # e2 holds another white pawn with legal moves
    assert widget._selected is not None
    assert widget._selected.notation == "e2"


def test_deselect_clears_all_selection_state():
    """After deselect, selected piece, legal targets, and message are cleared."""
    widget = _widget()
    widget._try_select("e2")
    assert widget._selected is not None
    widget._deselect()
    assert widget._selected is None
    assert widget._legal_targets == set()
    assert widget._message == ""


def test_status_markup_active_white():
    """Active game, WHITE to move: markup contains 'White'."""
    assert "White" in _widget()._status_markup()


def test_status_markup_active_black():
    """Active game, BLACK to move: markup contains 'Black'."""
    widget = _widget()
    widget._state = Game(
        board=Game.initial().board,
        turn=Color.BLACK,
        history=[],
        status=GameStatus.ACTIVE,
    )
    assert "Black" in widget._status_markup()


def test_status_markup_check():
    """CHECK status: markup mentions 'check' (case-insensitive)."""
    widget = _widget()
    widget._state = Game(
        board=Board(
            {
                _pos("e1"): _piece(PieceType.KING, Color.WHITE),
                _pos("e8"): _piece(PieceType.ROOK, Color.BLACK),
                _pos("a8"): _piece(PieceType.KING, Color.BLACK),
            }
        ),
        turn=Color.WHITE,
        history=[],
        status=GameStatus.CHECK,
    )
    assert "check" in widget._status_markup().lower()


def test_status_markup_checkmate(fools_mate_state):
    """Checkmate: markup contains 'Checkmate'."""
    widget = _widget()
    widget._state = fools_mate_state
    assert "Checkmate" in widget._status_markup()


def test_status_markup_stalemate():
    """Stalemate: markup contains 'Stalemate'."""
    widget = _widget()
    widget._state = _game_with_status(GameStatus.STALEMATE)
    assert "Stalemate" in widget._status_markup()


def test_history_markup_empty():
    """No moves yet: the placeholder '—' appears in the markup."""
    assert "—" in _widget()._history_markup()


def test_history_markup_shows_move_after_e2e4(apply_moves):
    """After 1.e2-e4 the history panel contains both square names."""
    widget = _widget()
    widget._state = apply_moves(["e2e4"])
    markup = widget._history_markup()
    assert "e2" in markup
    assert "e4" in markup


def test_captured_markup_no_captures():
    """With no captures yet, both sides show the '—' placeholder (appears twice)."""
    markup = _widget()._captured_markup()
    assert markup.count("—") == 2


def test_captured_markup_after_capture(apply_moves):
    """After White captures a Black pawn on d5, the black-pawn symbol (♟) appears."""
    widget = _widget()
    widget._state = apply_moves(["e2e4", "d7d5", "e4d5"])
    assert "♟" in widget._captured_markup()


def test_app_starts_without_crash():
    """The full ChessApp launches and exits cleanly via run_test()."""

    async def _run() -> None:
        async with ChessApp().run_test(size=(120, 50)) as pilot:
            await pilot.pause(0.1)

    asyncio.run(_run())


def test_cursor_up_increases_rank():
    """Pressing ↑ twice increases _cursor_rank by 2 (e2 → e4 cursor position)."""

    async def _run() -> None:
        async with ChessApp().run_test(size=(120, 50)) as pilot:
            await pilot.pause(0.1)
            board = pilot.app.query_one(BoardWidget)
            initial_rank = board._cursor_rank
            await pilot.press("up", "up")
            await pilot.pause(0.05)
            assert board._cursor_rank == initial_rank + 2

    asyncio.run(_run())


def test_cursor_clamps_at_rank_8():
    """Pressing ↑ eight times from rank_idx=1 should clamp at rank_idx=7 (rank 8)."""

    async def _run() -> None:
        async with ChessApp().run_test(size=(120, 50)) as pilot:
            await pilot.pause(0.1)
            board = pilot.app.query_one(BoardWidget)
            await pilot.press(*["up"] * 8)
            await pilot.pause(0.05)
            assert board._cursor_rank == 7

    asyncio.run(_run())


def test_select_and_move_e2_e4():
    """Enter on e2 selects the pawn; ↑↑ Enter completes the move to e4."""

    async def _run() -> None:
        async with ChessApp().run_test(size=(120, 50)) as pilot:
            await pilot.pause(0.1)
            board = pilot.app.query_one(BoardWidget)
            await pilot.press("enter")
            assert board._selected is not None
            assert board._selected.notation == "e2"
            await pilot.press("up", "up", "enter")
            await pilot.pause(0.05)
            assert board._selected is None
            assert board._state.board.get(_pos("e4")) is not None
            assert board._state.turn == Color.BLACK

    asyncio.run(_run())


def test_escape_deselects():
    """Pressing Escape after selecting a piece clears the selection."""

    async def _run() -> None:
        async with ChessApp().run_test(size=(120, 50)) as pilot:
            await pilot.pause(0.1)
            board = pilot.app.query_one(BoardWidget)
            await pilot.press("enter")
            assert board._selected is not None
            await pilot.press("escape")
            await pilot.pause(0.05)
            assert board._selected is None

    asyncio.run(_run())
