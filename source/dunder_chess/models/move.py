from pydantic import BaseModel, ConfigDict, computed_field

from .piece import Piece
from .position import Position


class Move(BaseModel):
    """A validated, applied move recorded in history."""

    model_config = ConfigDict(frozen=True)

    piece: Piece
    captured_piece: Piece | None = None
    from_position: Position
    to_position: Position

    @computed_field
    @property
    def notation(self) -> str:
        """Human-readable algebraic description of the move, e.g. ``'e2 → e4'``."""
        return f"{self.from_position.notation} → {self.to_position.notation}"
