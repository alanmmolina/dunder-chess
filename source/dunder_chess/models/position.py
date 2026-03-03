from typing import Self

from pydantic import BaseModel, ConfigDict, Field, computed_field


class Position(BaseModel):
    """
    A square on the chess board identified by file (a-h) and rank (1-8).
    """

    model_config = ConfigDict(frozen=True)

    file: str = Field(pattern=r"^[a-h]$")
    rank: int = Field(ge=1, le=8)

    @computed_field
    @property
    def notation(self) -> str:
        """Algebraic notation for this square, e.g. ``"e4"``."""
        return f"{self.file}{self.rank}"

    @computed_field
    @property
    def file_index(self) -> int:
        """0-based file index (a=0 … h=7)."""
        return ord(self.file) - ord("a")

    @computed_field
    @property
    def rank_index(self) -> int:
        """0-based rank index (rank 1=0 … rank 8=7)."""
        return self.rank - 1

    @classmethod
    def from_notation(cls, notation: str) -> Self:
        """Parse algebraic notation (e.g. ``"e4"``) into a Position."""
        if len(notation) != 2:
            raise ValueError(f"Invalid position notation: {notation!r}")
        return cls(file=notation[0], rank=int(notation[1]))

    @classmethod
    def from_indices(cls, file_idx: int, rank_idx: int) -> Self:
        """Construct from 0-based file and rank indices."""
        return cls(file=chr(ord("a") + file_idx), rank=rank_idx + 1)
