import pytest

from source.models.board import Board
from source.models.piece import Color, Piece, PieceType
from source.models.position import Position


def _pos(notation: str) -> Position:
    return Position.from_notation(notation)


def _piece(piece_type: PieceType, color: Color = Color.WHITE) -> Piece:
    return Piece(type=piece_type, color=color)


def test_getitem_returns_piece_on_occupied_square():
    """
    Arrange: a board with a white rook on e4.
    Act: index the board directly with board[e4].
    Assert: the piece returned matches the one placed there.
    """
    rook = _piece(PieceType.ROOK)
    board = Board({_pos("e4"): rook})
    assert board[_pos("e4")] == rook


def test_getitem_raises_for_empty_square():
    """
    Arrange: an empty board with no pieces.
    Act: index the board with board[e4].
    Assert: KeyError — the square is not occupied and has no entry in the mapping.
    """
    board = Board()
    with pytest.raises(KeyError):
        _ = board[_pos("e4")]


def test_contains_true_for_occupied_square():
    """
    Arrange: a board with a white pawn on d5.
    Act: check membership with d5 in board.
    Assert: True — the square is in the mapping.
    """
    board = Board({_pos("d5"): _piece(PieceType.PAWN)})
    assert _pos("d5") in board


def test_contains_false_for_empty_square():
    """
    Arrange: a board with a white pawn on d5.
    Act: check membership with e5 in board.
    Assert: False — e5 was never placed and is not in the mapping.
    """
    board = Board({_pos("d5"): _piece(PieceType.PAWN)})
    assert _pos("e5") not in board


def test_contains_false_for_non_position_object():
    """
    Arrange: a board with a single piece.
    Act: check membership with a plain string "e4" in board.
    Assert: False — __contains__ only matches Position instances, not raw strings.
    """
    board = Board({_pos("e4"): _piece(PieceType.PAWN)})
    assert "e4" not in board


def test_len_empty_board_is_zero():
    """
    Arrange: an empty board with no pieces.
    Act: call len(board).
    Assert: 0 — no squares are occupied.
    """
    assert len(Board()) == 0


def test_len_single_piece_is_one():
    """
    Arrange: a board with exactly one piece placed on e4.
    Act: call len(board).
    Assert: 1 — only one square is occupied.
    """
    board = Board({_pos("e4"): _piece(PieceType.PAWN)})
    assert len(board) == 1


def test_len_initial_board_has_32_pieces():
    """
    Arrange: the standard starting position via Board.initial().
    Act: call len(board).
    Assert: 32 — 16 white and 16 black pieces are placed at game start.
    """
    assert len(Board.initial()) == 32


def test_get_returns_piece_on_occupied_square():
    """
    Arrange: a board with a white bishop on c3.
    Act: call board.get(c3).
    Assert: the bishop is returned — the square is occupied.
    """
    bishop = _piece(PieceType.BISHOP)
    board = Board({_pos("c3"): bishop})
    assert board.get(_pos("c3")) == bishop


def test_get_returns_none_for_empty_square():
    """
    Arrange: a board with a white bishop on c3.
    Act: call board.get(d4) — a square with no piece.
    Assert: None — the square is unoccupied and no default was given.
    """
    board = Board({_pos("c3"): _piece(PieceType.BISHOP)})
    assert board.get(_pos("d4")) is None


def test_items_returns_all_position_piece_pairs():
    """
    Arrange: a board with two pieces — a white king on e1 and a black queen on d8.
    Act: call board.items().
    Assert: the list contains exactly those two (position, piece) pairs.
    """
    white_king = _piece(PieceType.KING)
    black_queen = _piece(PieceType.QUEEN, Color.BLACK)
    board = Board({_pos("e1"): white_king, _pos("d8"): black_queen})
    items = board.items()
    assert (_pos("e1"), white_king) in items
    assert (_pos("d8"), black_queen) in items
    assert len(items) == 2


def test_items_empty_board_returns_empty_list():
    """
    Arrange: an empty board with no pieces.
    Act: call board.items().
    Assert: an empty list — there are no occupied squares to enumerate.
    """
    assert Board().items() == []


def test_place_returns_new_board_with_piece_added():
    """
    Arrange: an empty board and a white knight.
    Act: call board.place(g1, knight).
    Assert: the returned board contains the knight on g1.
    """
    knight = _piece(PieceType.KNIGHT)
    new_board = Board().place(_pos("g1"), knight)
    assert new_board.get(_pos("g1")) == knight


def test_place_does_not_mutate_original_board():
    """
    Arrange: an empty board stored as a reference.
    Act: call board.place(g1, knight) and discard the result.
    Assert: the original board is still empty — Board is immutable.
    """
    original = Board()
    original.place(_pos("g1"), _piece(PieceType.KNIGHT))
    assert len(original) == 0


def test_place_replaces_existing_occupant():
    """
    Arrange: a board with a white pawn on e4.
    Act: call board.place(e4, black_rook) — the same square already has a piece.
    Assert: the new board holds the black rook on e4, replacing the pawn.
    """
    board = Board({_pos("e4"): _piece(PieceType.PAWN)})
    black_rook = _piece(PieceType.ROOK, Color.BLACK)
    new_board = board.place(_pos("e4"), black_rook)
    assert new_board.get(_pos("e4")) == black_rook
    assert len(new_board) == 1


def test_remove_returns_new_board_without_piece():
    """
    Arrange: a board with a white pawn on e4.
    Act: call board.remove(e4).
    Assert: the returned board no longer contains any piece on e4.
    """
    board = Board({_pos("e4"): _piece(PieceType.PAWN)})
    new_board = board.remove(_pos("e4"))
    assert _pos("e4") not in new_board


def test_remove_does_not_affect_other_squares():
    """
    Arrange: a board with a white pawn on e4 and a black rook on e8.
    Act: call board.remove(e4).
    Assert: the black rook on e8 remains on the returned board.
    """
    board = Board(
        {_pos("e4"): _piece(PieceType.PAWN), _pos("e8"): _piece(PieceType.ROOK, Color.BLACK)}
    )
    new_board = board.remove(_pos("e4"))
    assert _pos("e8") in new_board


def test_remove_does_not_mutate_original_board():
    """
    Arrange: a board with a white pawn on e4 stored as a reference.
    Act: call board.remove(e4) and discard the result.
    Assert: the original board still has the pawn on e4 — Board is immutable.
    """
    board = Board({_pos("e4"): _piece(PieceType.PAWN)})
    board.remove(_pos("e4"))
    assert _pos("e4") in board


def test_remove_is_noop_for_unoccupied_square():
    """
    Arrange: a board with a white pawn on e4.
    Act: call board.remove(d5) — a square that has no piece.
    Assert: the returned board is equal to the original — nothing was changed.
    """
    board = Board({_pos("e4"): _piece(PieceType.PAWN)})
    new_board = board.remove(_pos("d5"))
    assert new_board == board


def test_king_position_returns_white_king_square():
    """
    Arrange: a board with a white king on e1 and a black king on e8.
    Act: call board.king_position(WHITE).
    Assert: e1 is returned — the white king's square.
    """
    board = Board(
        {_pos("e1"): _piece(PieceType.KING), _pos("e8"): _piece(PieceType.KING, Color.BLACK)}
    )
    assert board.king_position(Color.WHITE) == _pos("e1")


def test_king_position_returns_black_king_square():
    """
    Arrange: a board with a white king on e1 and a black king on e8.
    Act: call board.king_position(BLACK).
    Assert: e8 is returned — the black king's square.
    """
    board = Board(
        {_pos("e1"): _piece(PieceType.KING), _pos("e8"): _piece(PieceType.KING, Color.BLACK)}
    )
    assert board.king_position(Color.BLACK) == _pos("e8")


def test_king_position_raises_when_king_is_absent():
    """
    Arrange: a board containing only a black king — the white king is missing.
    Act: call board.king_position(WHITE).
    Assert: ValueError — a missing king is an invariant violation.
    """
    board = Board({_pos("e8"): _piece(PieceType.KING, Color.BLACK)})
    with pytest.raises(ValueError):
        board.king_position(Color.WHITE)


def test_king_position_white_on_initial_board():
    """
    Arrange: standard starting position via Board.initial().
    Act: call board.king_position(WHITE).
    Assert: e1 — the white king's home square per chess convention.
    """
    assert Board.initial().king_position(Color.WHITE) == _pos("e1")


def test_king_position_black_on_initial_board():
    """
    Arrange: standard starting position via Board.initial().
    Act: call board.king_position(BLACK).
    Assert: e8 — the black king's home square per chess convention.
    """
    assert Board.initial().king_position(Color.BLACK) == _pos("e8")
