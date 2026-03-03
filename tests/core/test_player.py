from source.core.player import (
    apply_move,
    evaluate_game,
    evaluate_moves,
)
from source.core.rules import is_attacked, is_in_check
from source.models.board import Board
from source.models.game import Game, GameStatus
from source.models.piece import Color, Piece, PieceType
from source.models.position import Position


def _pos(notation: str) -> Position:
    return Position.from_notation(notation)


def _piece(piece_type: PieceType, color: Color = Color.WHITE) -> Piece:
    return Piece(type=piece_type, color=color)


def test_square_attacked_by_rook_on_same_file():
    """
    Arrange: black rook on e8 with white king on e1, same file, no blockers.
    Act: is_attacked(e1, BLACK).
    Assert: the rook's line-of-attack covers e1, so the square is attacked.
    """
    board = {
        _pos("e1"): _piece(PieceType.KING),
        _pos("e8"): _piece(PieceType.ROOK, Color.BLACK),
    }
    assert is_attacked(_pos("e1"), Color.BLACK, board) is True


def test_square_not_attacked_when_blocked():
    """
    Arrange: black rook on e8, friendly pawn interposed on e4, target square e1.
    Act: is_attacked(e1, BLACK).
    Assert: the interposing piece breaks the rook's ray, so e1 is not attacked.
    """
    board = {
        _pos("e1"): _piece(PieceType.KING),
        _pos("e4"): _piece(PieceType.PAWN),
        _pos("e8"): _piece(PieceType.ROOK, Color.BLACK),
    }
    assert is_attacked(_pos("e1"), Color.BLACK, board) is False


def test_square_attacked_by_pawn_diagonal():
    """
    Arrange: black pawn on d5; e4 is one of the pawn's attack diagonals.
    Act: is_attacked(e4, BLACK).
    Assert: True — pawns attack diagonally forward, not straight.
    """
    board = {_pos("d5"): _piece(PieceType.PAWN, Color.BLACK)}
    assert is_attacked(_pos("e4"), Color.BLACK, board) is True


def test_square_not_attacked_by_pawn_straight():
    """
    Arrange: black pawn on e5, directly above e4.
    Act: is_attacked(e4, BLACK).
    Assert: False — pawn pushes are not attack moves, so e4 is safe.
    """
    board = {_pos("e5"): _piece(PieceType.PAWN, Color.BLACK)}
    assert is_attacked(_pos("e4"), Color.BLACK, board) is False


def test_not_in_check_at_start(initial_state):
    """
    Arrange: initial board — all pieces behind their respective pawn screens.
    Act: is_in_check for both colors.
    Assert: neither king is under attack at game start.
    """
    assert is_in_check(Color.WHITE, initial_state.board) is False
    assert is_in_check(Color.BLACK, initial_state.board) is False


def test_is_in_check_detects_rook_attack(check_board):
    """
    Arrange: white king on e1 with a black rook on e8 aiming down the e-file.
    Act: is_in_check(WHITE).
    Assert: the king is in check; the rook's ray reaches e1.
    """
    assert is_in_check(Color.WHITE, check_board) is True


def test_white_opening_legal_move_count(initial_state):
    """
    Arrange: initial position — 8 pawns each with 2 pushes and 4 knights with
    2 jumps each.
    Act: gather all white legal moves.
    Assert: standard chess dictates exactly 20 legal moves on White's first turn.
    """
    total = sum(
        len(evaluate_moves(pos, initial_state))
        for pos, piece in initial_state.board.items()
        if piece.color == Color.WHITE
    )
    assert total == 20


def test_evaluate_moves_wrong_color_returns_empty(initial_state):
    """
    Arrange: initial state with WHITE to move; e7 holds a black pawn.
    Act: evaluate_moves on that black pawn's square.
    Assert: empty — you cannot move the opponent's pieces on your turn.
    """
    assert evaluate_moves(_pos("e7"), initial_state) == []


def test_evaluate_moves_empty_square_returns_empty(initial_state):
    """
    Arrange: initial state; e4 is an empty square in the middle of the board.
    Act: evaluate_moves on e4.
    Assert: empty — there is no piece there to generate moves for.
    """
    assert evaluate_moves(_pos("e4"), initial_state) == []


def test_evaluate_moves_pinned_piece_has_no_legal_moves():
    """
    Arrange: white king on e1, white bishop on e4, black rook on e8 — the bishop
    sits between the king and the rook on the same file, making it absolutely pinned.
    Act: evaluate_moves(e4).
    Assert: empty — any move by the bishop would expose the king to the rook.
    """
    board = Board(
        {
            _pos("e1"): _piece(PieceType.KING),
            _pos("e4"): _piece(PieceType.BISHOP),
            _pos("e8"): _piece(PieceType.ROOK, Color.BLACK),
            _pos("a8"): _piece(PieceType.KING, Color.BLACK),
        }
    )
    state = Game(board=board, turn=Color.WHITE, history=[], status=GameStatus.ACTIVE)
    assert evaluate_moves(_pos("e4"), state) == []


def test_evaluate_moves_king_can_escape_check():
    """
    Arrange: white king on e1 attacked by black rook on e8; d1 and f1 are empty
    and off the e-file.
    Act: evaluate_moves for the king at e1.
    Assert: d1 and f1 are legal destinations — the king has escape squares away from
    the rook's file.
    """
    board = Board(
        {
            _pos("e1"): _piece(PieceType.KING),
            _pos("e8"): _piece(PieceType.ROOK, Color.BLACK),
            _pos("a8"): _piece(PieceType.KING, Color.BLACK),
        }
    )
    state = Game(board=board, turn=Color.WHITE, history=[], status=GameStatus.CHECK)
    destinations = evaluate_moves(_pos("e1"), state)
    assert _pos("d1") in destinations
    assert _pos("f1") in destinations
    assert _pos("e2") not in destinations  # still on the e-file — covered by the rook


def test_evaluate_moves_piece_can_interpose_to_resolve_check():
    """
    Arrange: white king on e1 in check from black rook on e8; white rook on a4 can
    step to e4 to interpose along the e-file.
    Act: evaluate_moves for the white rook on a4.
    Assert: e4 is a legal destination — moving there blocks the check.
    """
    board = Board(
        {
            _pos("e1"): _piece(PieceType.KING),
            _pos("a4"): _piece(PieceType.ROOK),
            _pos("e8"): _piece(PieceType.ROOK, Color.BLACK),
            _pos("a8"): _piece(PieceType.KING, Color.BLACK),
        }
    )
    state = Game(board=board, turn=Color.WHITE, history=[], status=GameStatus.CHECK)
    destinations = evaluate_moves(_pos("a4"), state)
    assert _pos("e4") in destinations


def test_evaluate_moves_irrelevant_piece_has_no_moves_while_in_check():
    """
    Arrange: white king on e1 in check from black rook on e8; white pawn on h6
    can only advance to h7, which does nothing to resolve the check.
    Act: evaluate_moves for the pawn on h6.
    Assert: empty — a piece with no way to resolve the check cannot move legally.
    """
    board = Board(
        {
            _pos("e1"): _piece(PieceType.KING),
            _pos("h6"): _piece(PieceType.PAWN),
            _pos("e8"): _piece(PieceType.ROOK, Color.BLACK),
            _pos("a8"): _piece(PieceType.KING, Color.BLACK),
        }
    )
    state = Game(board=board, turn=Color.WHITE, history=[], status=GameStatus.CHECK)
    assert evaluate_moves(_pos("h6"), state) == []


def test_evaluate_game_active_at_start(initial_state):
    """
    Arrange: initial position — no attacks on either king, many legal moves available.
    Act: evaluate_game.
    Assert: ACTIVE — neither check nor stalemate applies at the start.
    """
    assert evaluate_game(initial_state) == GameStatus.ACTIVE


def test_evaluate_game_check_for_white(check_board):
    """
    Arrange: white king on e1 with a black rook on e8 aiming down the open e-file.
    Act: evaluate_game with WHITE as the current side.
    Assert: CHECK — the king is under attack but still has legal moves.
    """
    state = Game(board=check_board, turn=Color.WHITE, history=[], status=GameStatus.ACTIVE)
    assert evaluate_game(state) == GameStatus.CHECK


def test_evaluate_game_check_for_black():
    """
    Arrange: black king on e8 with a white rook on e1 aiming up the open e-file.
    Act: evaluate_game with BLACK to move.
    Assert: CHECK — check detection is symmetric and works for either side.
    """
    board = Board(
        {
            _pos("a1"): _piece(PieceType.KING),
            _pos("e1"): _piece(PieceType.ROOK),
            _pos("e8"): _piece(PieceType.KING, Color.BLACK),
        }
    )
    state = Game(board=board, turn=Color.BLACK, history=[], status=GameStatus.ACTIVE)
    assert evaluate_game(state) == GameStatus.CHECK


def test_evaluate_game_checkmate(fools_mate_state):
    """
    Arrange: state after Fool's Mate (1.f3 e5 2.g4 Qh4#) — white king has no escape.
    Act: inspect the status on the resulting Game.
    Assert: CHECKMATE — the fastest possible checkmate in chess.
    """
    assert fools_mate_state.status == GameStatus.CHECKMATE


def test_evaluate_game_stalemate(stalemate_state):
    """
    Arrange: white queen on f7 and white king on h6 trap black king on h8 — no legal
    moves remain but the king is not currently in check.
    Act: evaluate_game.
    Assert: STALEMATE — no moves without check is a draw, not a win.
    """
    assert evaluate_game(stalemate_state) == GameStatus.STALEMATE


def test_apply_move_from_empty_square_returns_none(initial_state):
    """
    Arrange: initial state; e4 is an empty square with no piece.
    Act: apply_move from e4 to e5.
    Assert: None — there is no piece to move from an empty square.
    """
    assert apply_move(_pos("e4"), _pos("e5"), initial_state) is None


def test_apply_move_wrong_color_returns_none(initial_state):
    """
    Arrange: initial state with WHITE to move; black pawn sits on e7.
    Act: apply_move the black pawn to e5.
    Assert: None — a player cannot move the opponent's pieces.
    """
    assert apply_move(_pos("e7"), _pos("e5"), initial_state) is None


def test_apply_move_geometrically_impossible_returns_none(initial_state):
    """
    Arrange: initial state; e2 holds a pawn that cannot leap to e5 in one move.
    Act: apply_move e2 → e5.
    Assert: None — destinations outside a piece's legal move set are rejected.
    """
    assert apply_move(_pos("e2"), _pos("e5"), initial_state) is None


def test_apply_move_illegal_when_leaving_king_in_check():
    """
    Arrange: white king e1, white bishop e4 pinned by black rook e8 on the same file.
    Act: move the bishop to d5, breaking the pin and exposing the king.
    Assert: None — any move that leaves the own king in check is illegal.
    """
    board = Board(
        {
            _pos("e1"): _piece(PieceType.KING),
            _pos("e4"): _piece(PieceType.BISHOP),
            _pos("e8"): _piece(PieceType.ROOK, Color.BLACK),
            _pos("a8"): _piece(PieceType.KING, Color.BLACK),
        }
    )
    state = Game(board=board, turn=Color.WHITE, history=[], status=GameStatus.ACTIVE)
    assert apply_move(_pos("e4"), _pos("d5"), state) is None


def test_apply_move_updates_board(initial_state):
    """
    Arrange: initial state with white pawn on e2.
    Act: apply_move e2 → e4; inspect the resulting board.
    Assert: e4 is now occupied and e2 is vacated.
    """
    new_state = apply_move(_pos("e2"), _pos("e4"), initial_state)
    assert new_state is not None
    assert _pos("e4") in new_state.board
    assert _pos("e2") not in new_state.board


def test_apply_move_flips_turn(initial_state):
    """
    Arrange: initial state with WHITE to move.
    Act: apply_move e2→e4.
    Assert: the active side flips to BLACK after every ply.
    """
    new_state = apply_move(_pos("e2"), _pos("e4"), initial_state)
    assert new_state is not None
    assert new_state.turn == Color.BLACK


def test_apply_move_appends_history(initial_state):
    """
    Arrange: initial state with empty move history.
    Act: apply_move e2→e4.
    Assert: history grows to length 1 — the move is appended.
    """
    new_state = apply_move(_pos("e2"), _pos("e4"), initial_state)
    assert new_state is not None
    assert len(new_state.history) == 1


def test_apply_move_history_records_piece(initial_state):
    """
    Arrange: initial state with white pawn on e2.
    Act: apply_move e2→e4; inspect the last history entry.
    Assert: the recorded piece is a white PAWN — the move stores the moving piece.
    """
    new_state = apply_move(_pos("e2"), _pos("e4"), initial_state)
    assert new_state is not None
    last_move = new_state.history[-1]
    assert last_move.piece.type == PieceType.PAWN
    assert last_move.piece.color == Color.WHITE


def test_apply_move_history_records_positions(initial_state):
    """
    Arrange: initial state with white pawn on e2.
    Act: apply_move e2→e4; inspect the last history entry.
    Assert: from_position is e2 and to_position is e4 — both endpoints are stored.
    """
    new_state = apply_move(_pos("e2"), _pos("e4"), initial_state)
    assert new_state is not None
    last_move = new_state.history[-1]
    assert last_move.from_position == _pos("e2")
    assert last_move.to_position == _pos("e4")


def test_apply_move_records_capture(apply_moves):
    """
    Arrange: position after 1.e4 d5 — white pawn on e4 can capture the black pawn on d5.
    Act: apply_move e4xd5; inspect the last history entry.
    Assert: captured_piece is set to the black pawn.
    """
    state = apply_moves(["e2e4", "d7d5"])
    new_state = apply_move(_pos("e4"), _pos("d5"), state)
    assert new_state is not None
    last_move = new_state.history[-1]
    assert last_move.captured_piece is not None
    assert last_move.captured_piece.type == PieceType.PAWN


def test_apply_move_captured_piece_removed_from_board(apply_moves):
    """
    Arrange: position after 1.e4 d5 — white pawn on e4 can capture the black pawn on d5.
    Act: apply_move e4xd5; inspect the resulting board.
    Assert: d5 now holds the white pawn — the captured black pawn is gone.
    """
    state = apply_moves(["e2e4", "d7d5"])
    new_state = apply_move(_pos("e4"), _pos("d5"), state)
    assert new_state is not None
    assert _pos("d5") in new_state.board
    assert new_state.board[_pos("d5")].color == Color.WHITE


def test_apply_move_sets_status_to_active(initial_state):
    """
    Arrange: initial state — no special conditions.
    Act: apply_move e2→e4.
    Assert: resulting status is ACTIVE — a quiet opening move creates no special state.
    """
    new_state = apply_move(_pos("e2"), _pos("e4"), initial_state)
    assert new_state is not None
    assert new_state.status == GameStatus.ACTIVE


def test_apply_move_sets_status_to_check():
    """
    Arrange: white rook on h1, white king on a1, black king on e8 — the rook can
    slide to e1 and give check along the open e-file.
    Act: apply_move h1→e1.
    Assert: resulting status is CHECK — apply_move recomputes the status after each move.
    """
    board = Board(
        {
            _pos("a1"): _piece(PieceType.KING),
            _pos("h1"): _piece(PieceType.ROOK),
            _pos("e8"): _piece(PieceType.KING, Color.BLACK),
        }
    )
    state = Game(board=board, turn=Color.WHITE, history=[], status=GameStatus.ACTIVE)
    new_state = apply_move(_pos("h1"), _pos("e1"), state)
    assert new_state is not None
    assert new_state.status == GameStatus.CHECK
