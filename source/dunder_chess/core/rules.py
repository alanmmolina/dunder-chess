from collections.abc import Iterator

from ..models.board import Board
from ..models.piece import Color, Piece, PieceType
from ..models.position import Position

# different magnitudes → L-shape
_KNIGHT_DELTAS: tuple[tuple[int, int], ...] = tuple(
    (file, rank) for file in (-2, -1, 1, 2) for rank in (-2, -1, 1, 2) if abs(file) != abs(rank)
)
# both axes non-zero → diagonal
_BISHOP_RAYS: tuple[tuple[int, int], ...] = tuple(
    (file, rank) for file in (-1, 1) for rank in (-1, 1)
)
# exactly one axis non-zero → orthogonal
_ROOK_RAYS: tuple[tuple[int, int], ...] = tuple(
    (file, rank) for file in (-1, 0, 1) for rank in (-1, 0, 1) if bool(file) ^ bool(rank)
)
# any adjacent square → all 8 directions
_KING_DELTAS: tuple[tuple[int, int], ...] = tuple(
    (file, rank) for file in (-1, 0, 1) for rank in (-1, 0, 1) if (file, rank) != (0, 0)
)


def _in_bounds(file_idx: int, rank_idx: int) -> bool:
    """Return True if (file_idx, rank_idx) lies within the 8x8 board."""
    return 0 <= file_idx <= 7 and 0 <= rank_idx <= 7


def _ray(
    file_idx: int,
    rank_idx: int,
    file_delta: int,
    rank_delta: int,
    piece: Piece,
    board: Board,
) -> Iterator[Position]:
    """Yield squares along one direction, stopping at the first occupied square."""
    next_file = file_idx + file_delta
    next_rank = rank_idx + rank_delta
    while _in_bounds(next_file, next_rank):
        dest = Position.from_indices(next_file, next_rank)
        if occupant := board.get(dest):
            if occupant.color != piece.color:
                yield dest
            return
        yield dest
        next_file += file_delta
        next_rank += rank_delta


def _ray_squares(
    piece: Piece,
    position: Position,
    board: Board,
    rays: tuple[tuple[int, int], ...],
) -> list[Position]:
    """
    Collect all reachable squares along each of the given ray directions.

    Each ray is extended one square at a time until the board edge or a
    blocking piece is reached.  An opponent piece on the blocking square is
    included (capture); a friendly piece on it is excluded.
    """
    return [
        dest
        for file_delta, rank_delta in rays
        for dest in _ray(
            position.file_index,
            position.rank_index,
            file_delta,
            rank_delta,
            piece,
            board,
        )
    ]


def _jump_squares(
    piece: Piece,
    position: Position,
    board: Board,
    deltas: tuple[tuple[int, int], ...],
) -> list[Position]:
    """
    Collect all squares reachable in a single leap by the given offsets.

    Each (file_delta, rank_delta) pair is applied once to position.  Squares
    outside the board and squares occupied by a friendly piece are discarded.
    Squares occupied by an opponent are included.
    """
    file_idx = position.file_index
    rank_idx = position.rank_index
    return [
        dest
        for file_delta, rank_delta in deltas
        if _in_bounds(next_file := file_idx + file_delta, next_rank := rank_idx + rank_delta)
        for dest in (Position.from_indices(next_file, next_rank),)
        if (occupant := board.get(dest)) is None or occupant.color != piece.color
    ]


def _pawn_moves(piece: Piece, position: Position, board: Board) -> list[Position]:
    """
    Return squares a pawn can physically move to.

    Includes:
    - One-square forward push (blocked if the destination is occupied).
    - Two-square push from the starting rank (blocked if either intervening
      square is occupied).
    - Diagonal captures onto squares occupied by an opponent piece.

    Does *not* include en passant (removed from scope in this implementation).
    """
    direction = 1 if piece.color == Color.WHITE else -1
    start_rank = 2 if piece.color == Color.WHITE else 7
    file_idx = position.file_index
    rank_idx = position.rank_index
    result: list[Position] = []

    if _in_bounds(file_idx, rank_idx + direction):
        one_step = Position.from_indices(file_idx, rank_idx + direction)
        if one_step not in board:
            result.append(one_step)
            if position.rank == start_rank and _in_bounds(file_idx, rank_idx + 2 * direction):
                two_step = Position.from_indices(file_idx, rank_idx + 2 * direction)
                if two_step not in board:
                    result.append(two_step)

    result.extend(
        dest
        for file_delta in (-1, 1)
        if _in_bounds(next_file := file_idx + file_delta, next_rank := rank_idx + direction)
        for dest in (Position.from_indices(next_file, next_rank),)
        if (occupant := board.get(dest)) is not None and occupant.color != piece.color
    )

    return result


def _pawn_attacks(piece: Piece, position: Position) -> list[Position]:
    """
    Return the two diagonal squares a pawn *threatens*, regardless of occupancy.

    This is intentionally separate from _pawn_moves: a pawn does not capture
    forward, so its attack squares (used for check detection and castling
    validation) differ from its reachable move squares.
    """
    direction = 1 if piece.color == Color.WHITE else -1
    file_idx = position.file_index
    rank_idx = position.rank_index
    return [
        Position.from_indices(file_idx + file_delta, rank_idx + direction)
        for file_delta in (-1, 1)
        if _in_bounds(file_idx + file_delta, rank_idx + direction)
    ]


def moves(piece: Piece, position: Position, board: Board) -> list[Position]:
    """
    Return all squares piece can physically reach from position.

    Does not filter for check — callers that need check-safe destinations
    should use ``evaluate_moves`` from the player module instead.
    """
    match piece.type:
        case PieceType.PAWN:
            return _pawn_moves(piece=piece, position=position, board=board)
        case PieceType.KNIGHT:
            return _jump_squares(piece=piece, position=position, board=board, deltas=_KNIGHT_DELTAS)
        case PieceType.BISHOP:
            return _ray_squares(piece=piece, position=position, board=board, rays=_BISHOP_RAYS)
        case PieceType.ROOK:
            return _ray_squares(piece=piece, position=position, board=board, rays=_ROOK_RAYS)
        case PieceType.QUEEN:
            return _ray_squares(
                piece=piece, position=position, board=board, rays=_BISHOP_RAYS + _ROOK_RAYS
            )
        case PieceType.KING:
            return _jump_squares(piece=piece, position=position, board=board, deltas=_KING_DELTAS)


def attacks(piece: Piece, position: Position, board: Board) -> list[Position]:
    """
    Squares piece threatens. Pawns attack diagonally only; all others match moves().
    """
    if piece.type == PieceType.PAWN:
        return _pawn_attacks(piece, position)
    return moves(piece, position, board)


def is_attacked(position: Position, color: Color, board: Board) -> bool:
    """Return True if any piece of color can reach position."""
    for from_position, piece in board.items():
        if piece.color != color:
            continue
        if position in attacks(piece=piece, position=from_position, board=board):
            return True
    return False


def is_in_check(color: Color, board: Board) -> bool:
    """Return True if color's king is currently under attack."""
    return is_attacked(position=board.king_position(color=color), color=color.opponent, board=board)
