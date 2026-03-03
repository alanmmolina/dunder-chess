from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, computed_field


class PieceType(StrEnum):
    """The six standard chess piece types."""

    KING = "KING"
    QUEEN = "QUEEN"
    ROOK = "ROOK"
    BISHOP = "BISHOP"
    KNIGHT = "KNIGHT"
    PAWN = "PAWN"


class Color(StrEnum):
    """Side of the board: WHITE moves first, BLACK second."""

    WHITE = "WHITE"
    BLACK = "BLACK"

    @property
    def opponent(self) -> Self:
        """Return the opposing color."""
        return Color.BLACK if self == Color.WHITE else Color.WHITE


_SYMBOLS: dict[tuple[PieceType, Color], str] = {
    (PieceType.KING, Color.WHITE): "♔",
    (PieceType.QUEEN, Color.WHITE): "♕",
    (PieceType.ROOK, Color.WHITE): "♖",
    (PieceType.BISHOP, Color.WHITE): "♗",
    (PieceType.KNIGHT, Color.WHITE): "♘",
    (PieceType.PAWN, Color.WHITE): "♙",
    (PieceType.KING, Color.BLACK): "♚",
    (PieceType.QUEEN, Color.BLACK): "♛",
    (PieceType.ROOK, Color.BLACK): "♜",
    (PieceType.BISHOP, Color.BLACK): "♝",
    (PieceType.KNIGHT, Color.BLACK): "♞",
    (PieceType.PAWN, Color.BLACK): "♟",
}


class Piece(BaseModel):
    """An immutable chess piece identified by its type and color."""

    model_config = ConfigDict(frozen=True)

    type: PieceType
    color: Color

    @computed_field  # type: ignore[misc]
    @property
    def symbol(self) -> str:
        """Unicode chess symbol for rendering (e.g. ``♔`` for a white king)."""
        return _SYMBOLS[(self.type, self.color)]
