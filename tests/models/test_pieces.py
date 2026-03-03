import pytest
from pydantic import ValidationError

from dunder_chess.models.piece import Color, Piece, PieceType


def test_piece_type_has_six_members():
    """
    Arrange: the PieceType enum class.
    Act: collect all members into a list.
    Assert: exactly six — one per standard chess piece.
    """
    assert len(list(PieceType)) == 6


@pytest.mark.parametrize(
    "piece_type, expected",
    [
        (PieceType.KING, "KING"),
        (PieceType.QUEEN, "QUEEN"),
        (PieceType.ROOK, "ROOK"),
        (PieceType.BISHOP, "BISHOP"),
        (PieceType.KNIGHT, "KNIGHT"),
        (PieceType.PAWN, "PAWN"),
    ],
)
def test_piece_type_string_values(piece_type, expected):
    """
    Arrange: each PieceType member supplied by @parametrize.
    Act: compare the member to its raw string value.
    Assert: equal — PieceType is a StrEnum and each member equals its uppercase name.
    """
    assert piece_type == expected


def test_color_has_two_members():
    """
    Arrange: the Color enum class.
    Act: collect all members into a list.
    Assert: exactly two — WHITE and BLACK.
    """
    assert len(list(Color)) == 2


def test_color_white_string_value():
    """
    Arrange: Color.WHITE.
    Act: compare to the raw string "WHITE".
    Assert: equal — Color is a StrEnum.
    """
    assert Color.WHITE == "WHITE"


def test_color_black_string_value():
    """
    Arrange: Color.BLACK.
    Act: compare to the raw string "BLACK".
    Assert: equal — Color is a StrEnum.
    """
    assert Color.BLACK == "BLACK"


def test_color_white_opponent_is_black():
    """
    Arrange: Color.WHITE.
    Act: .opponent.
    Assert: Color.BLACK — the opponent property always returns the other side.
    """
    assert Color.WHITE.opponent == Color.BLACK


def test_color_black_opponent_is_white():
    """
    Arrange: Color.BLACK.
    Act: .opponent.
    Assert: Color.WHITE — the relationship is symmetric.
    """
    assert Color.BLACK.opponent == Color.WHITE


def test_color_opponent_is_self_inverse():
    """
    Arrange: Color.WHITE.
    Act: call .opponent twice.
    Assert: returns WHITE again — applying opponent twice is a no-op.
    """
    assert Color.WHITE.opponent.opponent == Color.WHITE


def test_piece_stores_type_correctly():
    """
    Arrange: a Piece constructed with type=ROOK, color=WHITE.
    Act: read piece.type.
    Assert: PieceType.ROOK — the type field holds the value passed at construction.
    """
    piece = Piece(type=PieceType.ROOK, color=Color.WHITE)
    assert piece.type == PieceType.ROOK


def test_piece_stores_color_correctly():
    """
    Arrange: a Piece constructed with type=ROOK, color=BLACK.
    Act: read piece.color.
    Assert: Color.BLACK — the color field holds the value passed at construction.
    """
    piece = Piece(type=PieceType.ROOK, color=Color.BLACK)
    assert piece.color == Color.BLACK


@pytest.mark.parametrize(
    "piece_type, color, expected",
    [
        (PieceType.KING, Color.WHITE, "♔"),
        (PieceType.QUEEN, Color.WHITE, "♕"),
        (PieceType.ROOK, Color.WHITE, "♖"),
        (PieceType.BISHOP, Color.WHITE, "♗"),
        (PieceType.KNIGHT, Color.WHITE, "♘"),
        (PieceType.PAWN, Color.WHITE, "♙"),
        (PieceType.KING, Color.BLACK, "♚"),
        (PieceType.QUEEN, Color.BLACK, "♛"),
        (PieceType.ROOK, Color.BLACK, "♜"),
        (PieceType.BISHOP, Color.BLACK, "♝"),
        (PieceType.KNIGHT, Color.BLACK, "♞"),
        (PieceType.PAWN, Color.BLACK, "♟"),
    ],
)
def test_piece_symbol(piece_type, color, expected):
    """
    Arrange: one of the 12 (piece_type, color) combinations supplied by @parametrize.
    Act: .symbol.
    Assert: each pair maps to the correct Unicode chess glyph used to render pieces
    in the terminal UI (e.g. white king ♔, black queen ♛,
    white pawn ♙, black pawn ♟).
    """
    assert Piece(type=piece_type, color=color).symbol == expected


def test_piece_type_field_is_frozen():
    """
    Arrange: a valid Piece instance.
    Act: attempt to reassign the type field.
    Assert: raises ValidationError — Piece is frozen and all fields are immutable.
    """
    piece = Piece(type=PieceType.PAWN, color=Color.WHITE)
    with pytest.raises(ValidationError):
        piece.type = PieceType.QUEEN  # type: ignore[misc]


def test_piece_color_field_is_frozen():
    """
    Arrange: a valid Piece instance.
    Act: attempt to reassign the color field.
    Assert: raises ValidationError — Piece uses ConfigDict(frozen=True) and is immutable.
    """
    piece = Piece(type=PieceType.PAWN, color=Color.WHITE)
    with pytest.raises(ValidationError):
        piece.color = Color.BLACK  # type: ignore[misc]
