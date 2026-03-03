import pytest

from dunder_chess.core.player import apply_move
from dunder_chess.models.board import Board
from dunder_chess.models.game import Game, GameStatus
from dunder_chess.models.piece import Color, Piece, PieceType
from dunder_chess.models.position import Position


@pytest.fixture
def initial_state() -> Game:
    """Return the standard starting Game."""
    return Game.initial()


@pytest.fixture
def apply_moves():
    """
    Return a helper that applies a sequence of move strings to a Game.
    Each string must be four characters of long algebraic notation (e.g. "e2e4").
    Raises AssertionError if any move is illegal.
    """

    def _apply(moves: list[str], state: Game | None = None) -> Game:
        s = state if state is not None else Game.initial()
        for mv in moves:
            assert len(mv) == 4, f"Move {mv!r} must be 4 chars (e.g. 'e2e4')"
            from_position = Position.from_notation(mv[:2])
            to_position = Position.from_notation(mv[2:])
            s = apply_move(from_position, to_position, s)
            assert s is not None, f"Move {mv!r} was rejected as illegal"
        return s

    return _apply


@pytest.fixture
def fools_mate_state(apply_moves) -> Game:
    """Return the state after Fool's Mate (1.f3 e5 2.g4 Qh4#) — CHECKMATE."""
    return apply_moves(["f2f3", "e7e5", "g2g4", "d8h4"])


@pytest.fixture
def check_board() -> Board:
    """
    Minimal board: White King e1, Black Rook e8.
    White king is in check along the e-file.
    """
    return Board(
        {
            Position.from_notation("e1"): Piece(type=PieceType.KING, color=Color.WHITE),
            Position.from_notation("e8"): Piece(type=PieceType.ROOK, color=Color.BLACK),
            Position.from_notation("a8"): Piece(type=PieceType.KING, color=Color.BLACK),
        }
    )


@pytest.fixture
def stalemate_state() -> Game:
    """
    Minimal state: White King h6, White Queen f7, Black King h8; Black to move.
    Black has no legal moves and is not in check — stalemate.
    """
    board = {
        Position.from_notation("h6"): Piece(type=PieceType.KING, color=Color.WHITE),
        Position.from_notation("f7"): Piece(type=PieceType.QUEEN, color=Color.WHITE),
        Position.from_notation("h8"): Piece(type=PieceType.KING, color=Color.BLACK),
    }
    return Game(
        board=board,
        turn=Color.BLACK,
        history=[],
        status=GameStatus.ACTIVE,
    )
