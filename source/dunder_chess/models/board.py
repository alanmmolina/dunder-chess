from pydantic import ConfigDict, RootModel

from ..utils.constants import FILES
from .piece import Color, Piece, PieceType
from .position import Position

_BACK_RANK_ORDER: tuple[PieceType, ...] = (
    PieceType.ROOK,
    PieceType.KNIGHT,
    PieceType.BISHOP,
    PieceType.QUEEN,
    PieceType.KING,
    PieceType.BISHOP,
    PieceType.KNIGHT,
    PieceType.ROOK,
)


class Board(RootModel[dict[Position, Piece]]):
    """
    Immutable mapping of occupied squares (Position → Piece).
    """

    model_config = ConfigDict(frozen=True)
    root: dict[Position, Piece] = {}

    def __getitem__(self, position: Position) -> Piece:
        """Return the piece at position. Raises KeyError if the square is empty."""
        return self.root[position]

    def __contains__(self, position: object) -> bool:
        """Return True if position is occupied."""
        return isinstance(position, Position) and position in self.root

    def __len__(self) -> int:
        """Return the number of occupied squares."""
        return len(self.root)

    def __iter__(self):
        """Iterate over all occupied positions."""
        return iter(self.root)

    def get(self, position: Position) -> Piece | None:
        """Return the piece at position, or None if the square is empty."""
        return self.root.get(position)

    def items(self) -> list[tuple[Position, Piece]]:
        """Return all (position, piece) pairs as a list."""
        return list(self.root.items())

    def values(self):
        """Return all pieces on the board."""
        return self.root.values()

    def place(self, position: Position, piece: Piece) -> "Board":
        """Return a new Board with piece placed on position (replaces any occupant)."""
        return Board({**self.root, position: piece})

    def remove(self, position: Position) -> "Board":
        """
        Return a new Board with the piece at position removed.
        Returns self unchanged if position is not occupied.
        """
        if position not in self.root:
            return self
        return Board({key: val for key, val in self.root.items() if key != position})

    def king_position(self, color: Color) -> Position:
        """Return the position of color's king. Raises ValueError if absent."""
        for position, piece in self.root.items():
            if piece.type == PieceType.KING and piece.color == color:
                return position
        raise ValueError(f"King not found for {color}")

    @classmethod
    def initial(cls) -> "Board":
        """Return the standard chess starting position."""
        squares: dict[Position, Piece] = {}
        for file, piece_type in zip(FILES, _BACK_RANK_ORDER, strict=True):
            squares[Position(file=file, rank=1)] = Piece(type=piece_type, color=Color.WHITE)
            squares[Position(file=file, rank=8)] = Piece(type=piece_type, color=Color.BLACK)
        for file in FILES:
            squares[Position(file=file, rank=2)] = Piece(type=PieceType.PAWN, color=Color.WHITE)
            squares[Position(file=file, rank=7)] = Piece(type=PieceType.PAWN, color=Color.BLACK)
        return cls(squares)
