import pytest
from pydantic import ValidationError

from source.models.move import Move
from source.models.piece import Color, Piece, PieceType
from source.models.position import Position


def _pos(notation: str) -> Position:
    return Position.from_notation(notation)


def _pawn(color: Color) -> Piece:
    return Piece(type=PieceType.PAWN, color=color)


def _king(color: Color) -> Piece:
    return Piece(type=PieceType.KING, color=color)


def test_move_notation_regular():
    """
    Arrange: a plain pawn move from e2 to e4 with no special flags.
    Act: read .notation.
    Assert: formats as "e2 → e4" using the unicode arrow separator.
    """
    move = Move(piece=_pawn(Color.WHITE), from_position=_pos("e2"), to_position=_pos("e4"))
    assert move.notation == "e2 → e4"


def test_move_notation_reflects_actual_positions():
    """
    Arrange: a knight move from g1 to f3.
    Act: read .notation.
    Assert: "g1 → f3" — notation always mirrors the stored from/to positions.
    """
    knight = Piece(type=PieceType.KNIGHT, color=Color.WHITE)
    move = Move(piece=knight, from_position=_pos("g1"), to_position=_pos("f3"))
    assert move.notation == "g1 → f3"


def test_move_notation_for_capture():
    """
    Arrange: a pawn captures an enemy piece — notation format is the same as a quiet move.
    Act: read .notation on a Move with captured_piece set.
    Assert: "d4 → e5" — the presence of a capture does not alter the notation format.
    """
    move = Move(
        piece=_pawn(Color.WHITE),
        from_position=_pos("d4"),
        to_position=_pos("e5"),
        captured_piece=_pawn(Color.BLACK),
    )
    assert move.notation == "d4 → e5"


def test_move_stores_piece_correctly():
    """
    Arrange: a white pawn used to construct a Move.
    Act: read move.piece.
    Assert: the stored piece matches the one passed at construction time.
    """
    pawn = _pawn(Color.WHITE)
    move = Move(piece=pawn, from_position=_pos("e2"), to_position=_pos("e4"))
    assert move.piece == pawn


def test_move_stores_from_position_correctly():
    """
    Arrange: a Move constructed with from_position e2.
    Act: read move.from_position.
    Assert: the stored position has notation "e2".
    """
    move = Move(piece=_pawn(Color.WHITE), from_position=_pos("e2"), to_position=_pos("e4"))
    assert move.from_position.notation == "e2"


def test_move_stores_to_position_correctly():
    """
    Arrange: a Move constructed with to_position e4.
    Act: read move.to_position.
    Assert: the stored position has notation "e4".
    """
    move = Move(piece=_pawn(Color.WHITE), from_position=_pos("e2"), to_position=_pos("e4"))
    assert move.to_position.notation == "e4"


def test_move_captured_piece_defaults_to_none():
    """
    Arrange: a Move constructed without specifying captured_piece.
    Act: read move.captured_piece.
    Assert: None — quiet moves carry no captured piece by default.
    """
    move = Move(piece=_pawn(Color.WHITE), from_position=_pos("e2"), to_position=_pos("e4"))
    assert move.captured_piece is None


def test_move_records_captured_piece():
    """
    Arrange: a pawn captures an enemy pawn on e5.
    Act: inspect captured_piece on the resulting Move.
    Assert: the captured piece is stored with its original color intact.
    """
    captured = Piece(type=PieceType.PAWN, color=Color.BLACK)
    move = Move(
        piece=_pawn(Color.WHITE),
        from_position=_pos("d4"),
        to_position=_pos("e5"),
        captured_piece=captured,
    )
    assert move.captured_piece is not None
    assert move.captured_piece.color == Color.BLACK


def test_move_captured_piece_preserves_type():
    """
    Arrange: a pawn captures a black rook.
    Act: read move.captured_piece.type.
    Assert: ROOK — the piece type of the captured piece is preserved exactly.
    """
    move = Move(
        piece=_pawn(Color.WHITE),
        from_position=_pos("a1"),
        to_position=_pos("a8"),
        captured_piece=Piece(type=PieceType.ROOK, color=Color.BLACK),
    )
    assert move.captured_piece is not None
    assert move.captured_piece.type == PieceType.ROOK


def test_move_from_position_is_frozen():
    """
    Arrange: a valid Move instance.
    Act: attempt to reassign from_position.
    Assert: raises ValidationError — Move is frozen and cannot be mutated.
    """
    move = Move(piece=_pawn(Color.WHITE), from_position=_pos("e2"), to_position=_pos("e4"))
    with pytest.raises(ValidationError):
        move.from_position = _pos("e3")  # type: ignore[misc]


def test_move_to_position_is_frozen():
    """
    Arrange: a valid Move instance.
    Act: attempt to reassign to_position.
    Assert: raises ValidationError — all fields on Move are immutable.
    """
    move = Move(piece=_pawn(Color.WHITE), from_position=_pos("e2"), to_position=_pos("e4"))
    with pytest.raises(ValidationError):
        move.to_position = _pos("e3")  # type: ignore[misc]


def test_move_piece_field_is_frozen():
    """
    Arrange: a valid Move instance.
    Act: attempt to reassign the piece field to a different piece.
    Assert: raises ValidationError — the piece that made the move cannot be changed.
    """
    move = Move(piece=_pawn(Color.WHITE), from_position=_pos("e2"), to_position=_pos("e4"))
    with pytest.raises(ValidationError):
        move.piece = _king(Color.WHITE)  # type: ignore[misc]


def test_move_captured_piece_field_is_frozen():
    """
    Arrange: a valid Move instance with a captured piece.
    Act: attempt to reassign captured_piece.
    Assert: raises ValidationError — captured information is permanent once recorded.
    """
    move = Move(
        piece=_pawn(Color.WHITE),
        from_position=_pos("d4"),
        to_position=_pos("e5"),
        captured_piece=_pawn(Color.BLACK),
    )
    with pytest.raises(ValidationError):
        move.captured_piece = None  # type: ignore[misc]
