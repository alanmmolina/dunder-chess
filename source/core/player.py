from ..models.game import Game, GameStatus
from ..models.move import Move
from ..models.piece import Piece
from ..models.position import Position
from .rules import is_in_check, moves


def evaluate_moves(position: Position, state: Game) -> list[Position]:
    """
    Return all legal destinations for the piece at position in the current state.

    Filters raw per-piece moves by simulating each candidate on a scratch board
    and discarding any that leave the moving side's king in check.
    Returns an empty list if the square is empty or belongs to the side not to move.
    """
    piece = state.board.get(position=position)
    if piece is None or piece.color != state.turn:
        return []

    destinations: list[Position] = []
    for destination in moves(piece=piece, position=position, board=state.board):
        _board = state.board.remove(position=position).place(position=destination, piece=piece)
        if not is_in_check(color=piece.color, board=_board):
            destinations.append(destination)
    return destinations


def evaluate_game(state: Game) -> GameStatus:
    """
    Determine the game status for the side that is now to move.

    Iterates over every piece belonging to that side and checks whether any
    of them have at least one legal move.  If none do:
    - The side is in check  — CHECKMATE (game over).
    - The side is not in check — STALEMATE (draw).
    Otherwise returns CHECK if the king is attacked, or ACTIVE.
    """
    color = state.turn
    has_moves = any(
        evaluate_moves(position=position, state=state)
        for position, piece in state.board.items()
        if piece.color == color
    )
    if not has_moves:
        return (
            GameStatus.CHECKMATE
            if is_in_check(color=color, board=state.board)
            else GameStatus.STALEMATE
        )
    if is_in_check(color=color, board=state.board):
        return GameStatus.CHECK
    return GameStatus.ACTIVE


def apply_move(
    from_position: Position,
    to_position: Position,
    state: Game,
) -> Game | None:
    """
    Validate, apply, and advance the game state in one step.

    Checks (in order):
    1. A piece of the current side exists on from_position.
    2. to_position is in the legal-move set for that piece (i.e. check-safe).

    On success returns the new ``Game`` snapshot with the turn flipped, the move
    appended to history, and the status recomputed.  Returns ``None`` if illegal.
    """
    piece = state.board.get(position=from_position)
    if piece is None or piece.color != state.turn:
        return None

    if to_position not in evaluate_moves(position=from_position, state=state):
        return None

    captured_piece: Piece | None = state.board.get(position=to_position)
    new_board = state.board.remove(position=from_position).place(position=to_position, piece=piece)
    move = Move(
        piece=piece,
        from_position=from_position,
        to_position=to_position,
        captured_piece=captured_piece,
    )

    next_state = Game(
        board=new_board,
        turn=state.turn.opponent,
        history=[*state.history, move],
        status=GameStatus.ACTIVE,
    )
    return next_state.model_copy(update={"status": evaluate_game(next_state)})
