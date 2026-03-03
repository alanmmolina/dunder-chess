import pytest
from pydantic import ValidationError

from source.models.game import GameStatus
from source.models.piece import Color, PieceType
from source.models.position import Position


def test_game_status_active_string_value():
    """
    Arrange: the GameStatus.ACTIVE member.
    Act: compare to its raw string value "ACTIVE".
    Assert: equal — GameStatus is a StrEnum and must expose the plain string.
    """
    assert GameStatus.ACTIVE == "ACTIVE"


def test_game_status_check_string_value():
    """
    Arrange: the GameStatus.CHECK member.
    Act: compare to its raw string value "CHECK".
    Assert: equal — StrEnum equality holds for all four members.
    """
    assert GameStatus.CHECK == "CHECK"


def test_game_status_checkmate_string_value():
    """
    Arrange: the GameStatus.CHECKMATE member.
    Act: compare to its raw string value "CHECKMATE".
    Assert: equal — confirms the exact spelling used throughout the engine.
    """
    assert GameStatus.CHECKMATE == "CHECKMATE"


def test_game_status_stalemate_string_value():
    """
    Arrange: the GameStatus.STALEMATE member.
    Act: compare to its raw string value "STALEMATE".
    Assert: equal — stalemate is a draw condition, distinct from checkmate.
    """
    assert GameStatus.STALEMATE == "STALEMATE"


def test_game_status_has_four_members():
    """
    Arrange: the GameStatus enum class.
    Act: collect all members into a list.
    Assert: exactly four — ACTIVE, CHECK, CHECKMATE, STALEMATE.
    """
    assert len(list(GameStatus)) == 4


def test_initial_state_has_32_pieces(initial_state):
    """
    Arrange: a freshly created game via Game.initial().
    Act: count the entries in the board dict.
    Assert: exactly 32 pieces — 16 per side — are present at the start.
    """
    assert len(initial_state.board) == 32


def test_initial_turn_is_white(initial_state):
    """
    Arrange: a freshly created game via Game.initial().
    Act: read turn.
    Assert: White always moves first per chess rules.
    """
    assert initial_state.turn == Color.WHITE


def test_initial_status_is_active(initial_state):
    """
    Arrange: a freshly created game via Game.initial().
    Act: check status.
    Assert: ACTIVE — no threats exist at game start, so neither CHECK nor STALEMATE applies.
    """
    assert initial_state.status == GameStatus.ACTIVE


def test_initial_history_is_empty(initial_state):
    """
    Arrange: a freshly created game via Game.initial().
    Act: check history.
    Assert: empty list — no moves have been made before the game starts.
    """
    assert initial_state.history == []


def test_initial_white_back_rank(initial_state):
    """
    Arrange: a freshly created game via Game.initial().
    Act: inspect each square on rank 1.
    Assert: pieces follow the standard RNBQKBNR order from left (a1) to right (h1).
    """
    expected = {
        "a1": PieceType.ROOK,
        "b1": PieceType.KNIGHT,
        "c1": PieceType.BISHOP,
        "d1": PieceType.QUEEN,
        "e1": PieceType.KING,
        "f1": PieceType.BISHOP,
        "g1": PieceType.KNIGHT,
        "h1": PieceType.ROOK,
    }
    for notation, piece_type in expected.items():
        assert initial_state.board[Position.from_notation(notation)].type == piece_type, notation


def test_initial_black_back_rank(initial_state):
    """
    Arrange: a freshly created game via Game.initial().
    Act: inspect each square on rank 8.
    Assert: pieces mirror white's setup in RNBQKBNR order from a8 to h8.
    """
    expected = {
        "a8": PieceType.ROOK,
        "b8": PieceType.KNIGHT,
        "c8": PieceType.BISHOP,
        "d8": PieceType.QUEEN,
        "e8": PieceType.KING,
        "f8": PieceType.BISHOP,
        "g8": PieceType.KNIGHT,
        "h8": PieceType.ROOK,
    }
    for notation, piece_type in expected.items():
        assert initial_state.board[Position.from_notation(notation)].type == piece_type, notation


def test_initial_white_pawns_on_rank_2(initial_state):
    """
    Arrange: a freshly created game via Game.initial().
    Act: check every square on rank 2.
    Assert: all 8 squares hold white pawns — the standard starting position.
    """
    for file in "abcdefgh":
        piece = initial_state.board[Position.from_notation(f"{file}2")]
        assert piece.type == PieceType.PAWN
        assert piece.color == Color.WHITE


def test_initial_black_pawns_on_rank_7(initial_state):
    """
    Arrange: a freshly created game via Game.initial().
    Act: check every square on rank 7.
    Assert: all 8 squares hold black pawns — the standard starting position.
    """
    for file in "abcdefgh":
        piece = initial_state.board[Position.from_notation(f"{file}7")]
        assert piece.type == PieceType.PAWN
        assert piece.color == Color.BLACK


def test_initial_middle_ranks_empty(initial_state):
    """
    Arrange: a freshly created game via Game.initial().
    Act: check all 32 squares in ranks 3 through 6.
    Assert: no pieces — the centre of the board starts empty before any moves.
    """
    for rank in range(3, 7):
        for file in "abcdefgh":
            assert Position.from_notation(f"{file}{rank}") not in initial_state.board


def test_game_state_is_frozen(initial_state):
    """
    Arrange: a valid Game instance.
    Act: attempt to reassign turn.
    Assert: raises an exception — Game uses ConfigDict(frozen=True); it is
    replaced by a new object after each move, never mutated in place.
    """
    with pytest.raises(ValidationError):
        initial_state.turn = Color.BLACK  # type: ignore[misc]


def test_game_board_field_is_frozen(initial_state):
    """
    Arrange: a valid Game instance.
    Act: attempt to reassign board to a new Board.
    Assert: raises ValidationError — all fields are frozen, not just turn.
    """
    from source.models.board import Board

    with pytest.raises(ValidationError):
        initial_state.board = Board()  # type: ignore[misc]


def test_game_history_field_is_frozen(initial_state):
    """
    Arrange: a valid Game instance with an empty history list.
    Act: attempt to reassign history to a new list.
    Assert: raises ValidationError — immutability covers every field.
    """
    with pytest.raises(ValidationError):
        initial_state.history = []  # type: ignore[misc]


def test_game_status_field_is_frozen(initial_state):
    """
    Arrange: a valid Game instance with status ACTIVE.
    Act: attempt to reassign status to CHECK.
    Assert: raises ValidationError — status cannot be changed directly.
    """
    with pytest.raises(ValidationError):
        initial_state.status = GameStatus.CHECK  # type: ignore[misc]


def test_initial_rank_1_pieces_are_white(initial_state):
    """
    Arrange: a freshly created game via Game.initial().
    Act: inspect the color of every piece on rank 1.
    Assert: all eight are white — rank 1 is White's home row.
    """
    for file in "abcdefgh":
        piece = initial_state.board[Position.from_notation(f"{file}1")]
        assert piece.color == Color.WHITE, f"{file}1 should be WHITE"


def test_initial_rank_8_pieces_are_black(initial_state):
    """
    Arrange: a freshly created game via Game.initial().
    Act: inspect the color of every piece on rank 8.
    Assert: all eight are black — rank 8 is Black's home row.
    """
    for file in "abcdefgh":
        piece = initial_state.board[Position.from_notation(f"{file}8")]
        assert piece.color == Color.BLACK, f"{file}8 should be BLACK"
