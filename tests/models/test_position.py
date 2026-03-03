import pytest
from pydantic import ValidationError

from dunder_chess.models.position import Position


def _pos(notation: str) -> Position:
    return Position.from_notation(notation)


def test_from_notation_parses_file_and_rank():
    """
    Arrange: valid 2-character notation string "e4".
    Act: Position.from_notation("e4").
    Assert: file="e" and rank=4 are stored correctly.
    """
    position = _pos("e4")
    assert position.file == "e"
    assert position.rank == 4


def test_from_notation_corner_a1():
    """
    Arrange: notation "a1" — the bottom-left corner of the board.
    Act: Position.from_notation("a1").
    Assert: file="a" and rank=1.
    """
    position = _pos("a1")
    assert position.file == "a"
    assert position.rank == 1


def test_from_notation_corner_h8():
    """
    Arrange: notation "h8" — the top-right corner of the board.
    Act: Position.from_notation("h8").
    Assert: file="h" and rank=8.
    """
    position = _pos("h8")
    assert position.file == "h"
    assert position.rank == 8


def test_from_indices_round_trips_to_notation():
    """
    Arrange: 0-based file_idx=4, rank_idx=3.
    Act: Position.from_indices(4, 3).
    Assert: "e4" — index-to-notation conversion is correct.
    """
    assert Position.from_indices(4, 3).notation == "e4"


def test_from_indices_a1_at_zero_zero():
    """
    Arrange: both indices at 0 — the minimum corner of the board.
    Act: Position.from_indices(0, 0).
    Assert: "a1".
    """
    assert Position.from_indices(0, 0).notation == "a1"


def test_from_indices_h8_at_seven_seven():
    """
    Arrange: both indices at 7 — the maximum corner of the board.
    Act: Position.from_indices(7, 7).
    Assert: "h8".
    """
    assert Position.from_indices(7, 7).notation == "h8"


def test_notation_reconstructs_from_parts():
    """
    Arrange: Position constructed directly with file="d", rank=7.
    Act: read .notation.
    Assert: "d7" — the computed field joins file and rank without a separator.
    """
    assert Position(file="d", rank=7).notation == "d7"


def test_notation_matches_from_notation_input():
    """
    Arrange: a Position parsed from "g3".
    Act: read .notation.
    Assert: "g3" — round-trip through from_notation preserves the original string.
    """
    assert _pos("g3").notation == "g3"


def test_file_index_a_is_zero():
    """
    Arrange: Position with file="a" — the leftmost file.
    Act: read .file_index.
    Assert: 0 — the 0-based index starts at 'a'.
    """
    assert Position(file="a", rank=1).file_index == 0


def test_file_index_h_is_seven():
    """
    Arrange: Position with file="h" — the rightmost file.
    Act: read .file_index.
    Assert: 7 — the 0-based index covers the full a-h range.
    """
    assert Position(file="h", rank=1).file_index == 7


def test_file_index_e_is_four():
    """
    Arrange: Position with file="e" — the middle file, commonly the king's starting file.
    Act: read .file_index.
    Assert: 4 — confirming the index is ord(file) - ord('a').
    """
    assert Position(file="e", rank=1).file_index == 4


def test_rank_index_rank_1_is_zero():
    """
    Arrange: Position with rank=1 — the lowest rank.
    Act: read .rank_index.
    Assert: 0 — rank_index is 0-based (rank - 1).
    """
    assert Position(file="a", rank=1).rank_index == 0


def test_rank_index_rank_8_is_seven():
    """
    Arrange: Position with rank=8 — the highest rank.
    Act: read .rank_index.
    Assert: 7 — the 0-based index tops out at 7.
    """
    assert Position(file="a", rank=8).rank_index == 7


def test_rank_index_rank_4_is_three():
    """
    Arrange: Position with rank=4 — the mid-board rank frequently targeted by pawns.
    Act: read .rank_index.
    Assert: 3 — confirming the index is rank - 1.
    """
    assert Position(file="e", rank=4).rank_index == 3


def test_equality_same_values():
    """
    Arrange: two Position instances with identical file and rank, created separately.
    Act: compare with ==.
    Assert: equal — Pydantic frozen models use structural (value) equality.
    """
    assert Position(file="c", rank=3) == Position(file="c", rank=3)


def test_inequality_different_file():
    """
    Arrange: two positions on the same rank but different files.
    Act: compare with ==.
    Assert: not equal — file is part of the identity of a square.
    """
    assert Position(file="c", rank=3) != Position(file="d", rank=3)


def test_inequality_different_rank():
    """
    Arrange: two positions on the same file but different ranks.
    Act: compare with ==.
    Assert: not equal — rank is part of the identity of a square.
    """
    assert Position(file="c", rank=3) != Position(file="c", rank=4)


def test_invalid_file_raises():
    """
    Arrange: file="z", which lies outside the valid a-h range.
    Act: construct Position.
    Assert: ValidationError — the regex field validator rejects characters outside [a-h].
    """
    with pytest.raises(ValidationError):
        Position(file="z", rank=4)


def test_rank_too_high_raises():
    """
    Arrange: rank=9, one beyond the maximum board boundary.
    Act: construct Position.
    Assert: ValidationError — rank must be ≤8 per the Field(le=8) constraint.
    """
    with pytest.raises(ValidationError):
        Position(file="e", rank=9)


def test_rank_zero_raises():
    """
    Arrange: rank=0, below the minimum board boundary.
    Act: construct Position.
    Assert: ValidationError — rank must be ≥1 per the Field(ge=1) constraint.
    """
    with pytest.raises(ValidationError):
        Position(file="e", rank=0)


def test_from_notation_wrong_length_raises():
    """
    Arrange: notation "e42" — three characters instead of the expected two.
    Act: Position.from_notation("e42").
    Assert: ValueError — the parser requires exactly "<file><rank>" format.
    """
    with pytest.raises(ValueError):
        Position.from_notation("e42")


def test_from_notation_bad_file_raises():
    """
    Arrange: notation "z4" where 'z' is not a valid board file.
    Act: Position.from_notation("z4").
    Assert: ValidationError or ValueError — the file character must be in a-h.
    """
    with pytest.raises((ValueError, ValidationError)):
        Position.from_notation("z4")


def test_rank_field_is_frozen():
    """
    Arrange: a valid Position instance.
    Act: attempt to reassign the rank field.
    Assert: raises ValidationError — Position uses ConfigDict(frozen=True).
    """
    position = _pos("e4")
    with pytest.raises(ValidationError):
        position.rank = 5  # type: ignore[misc]


def test_file_field_is_frozen():
    """
    Arrange: a valid Position instance.
    Act: attempt to reassign the file field.
    Assert: raises ValidationError — all fields on Position are immutable.
    """
    position = _pos("e4")
    with pytest.raises(ValidationError):
        position.file = "d"  # type: ignore[misc]
