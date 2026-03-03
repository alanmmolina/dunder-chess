from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict

from .board import Board
from .move import Move
from .piece import Color


class GameStatus(StrEnum):
    """
    Outcome of evaluating the board after a move.

    ACTIVE    — game in progress, no immediate threats.
    CHECK     — the side to move is in check but has at least one legal reply.
    CHECKMATE — the side to move is in check with no legal moves; game over.
    STALEMATE — the side to move is not in check but has no legal moves; draw.
    """

    ACTIVE = "ACTIVE"
    CHECK = "CHECK"
    CHECKMATE = "CHECKMATE"
    STALEMATE = "STALEMATE"


class Game(BaseModel):
    """Complete, immutable snapshot of a chess game at a single point in time."""

    model_config = ConfigDict(frozen=True)

    board: Board
    turn: Color
    history: list[Move]
    status: GameStatus

    @classmethod
    def initial(cls) -> Self:
        """Return a Game at the standard chess starting position."""
        return cls(
            board=Board.initial(),
            turn=Color.WHITE,
            history=[],
            status=GameStatus.ACTIVE,
        )
