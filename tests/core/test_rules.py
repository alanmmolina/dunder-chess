from source.core.rules import attacks, is_attacked, is_in_check, moves
from source.models.board import Board
from source.models.piece import Color, Piece, PieceType
from source.models.position import Position


def _pos(notation: str) -> Position:
    return Position.from_notation(notation)


def _piece(piece_type: PieceType, color: Color = Color.WHITE) -> Piece:
    return Piece(type=piece_type, color=color)


def _notations(positions: list[Position]) -> set[str]:
    return {p.notation for p in positions}


def test_pawn_one_and_two_step_from_start():
    """
    Arrange: white pawn on its starting square e2 with both e3 and e4 empty.
    Act: moves.
    Assert: the double-step advance is only available from the starting rank.
    """
    pawn = _piece(PieceType.PAWN)
    board = {_pos("e2"): pawn}
    result = moves(pawn, _pos("e2"), board)
    assert _notations(result) == {"e3", "e4"}


def test_pawn_one_step_only_when_not_on_start_rank():
    """
    Arrange: white pawn on e3 (already moved off its starting rank).
    Act: moves.
    Assert: only a single-step advance to e4 is offered; the double push is gone.
    """
    pawn = _piece(PieceType.PAWN)
    board = {_pos("e3"): pawn}
    result = moves(pawn, _pos("e3"), board)
    assert _notations(result) == {"e4"}


def test_pawn_blocked_by_own_piece():
    """
    Arrange: white pawn on e2 with a friendly rook on e3 directly ahead.
    Act: moves.
    Assert: pawns cannot push through any piece, so the result is empty.
    """
    pawn = _piece(PieceType.PAWN)
    board = {_pos("e2"): pawn, _pos("e3"): _piece(PieceType.ROOK)}
    result = moves(pawn, _pos("e2"), board)
    assert _notations(result) == set()


def test_pawn_two_step_blocked_if_one_step_square_occupied():
    """
    Arrange: white pawn on e2 with an enemy piece occupying the transit square e3.
    Act: moves.
    Assert: e4 is also unavailable because the double push requires e3 to be clear.
    """
    pawn = _piece(PieceType.PAWN)
    board = {_pos("e2"): pawn, _pos("e3"): _piece(PieceType.ROOK, Color.BLACK)}
    result = moves(pawn, _pos("e2"), board)
    assert "e4" not in _notations(result)


def test_pawn_diagonal_capture():
    """
    Arrange: white pawn on e4 with enemy pawns on both d5 and f5.
    Act: moves.
    Assert: both diagonal captures are included alongside the forward push.
    """
    pawn = _piece(PieceType.PAWN)
    board = {
        _pos("e4"): pawn,
        _pos("d5"): _piece(PieceType.PAWN, Color.BLACK),
        _pos("f5"): _piece(PieceType.PAWN, Color.BLACK),
    }
    result = moves(pawn, _pos("e4"), board)
    assert {"d5", "e5", "f5"} <= _notations(result)


def test_pawn_cannot_capture_friendly_diagonally():
    """
    Arrange: white pawn on e4 with a friendly rook on d5.
    Act: moves.
    Assert: d5 is excluded; pawns cannot capture friendly pieces.
    """
    pawn = _piece(PieceType.PAWN)
    board = {_pos("e4"): pawn, _pos("d5"): _piece(PieceType.ROOK)}
    result = moves(pawn, _pos("e4"), board)
    assert "d5" not in _notations(result)


def test_black_pawn_moves_downward():
    """
    Arrange: black pawn on its starting square e7 with e6 and e5 empty.
    Act: moves.
    Assert: black pawns advance toward rank 1, so e6 and e5 are the targets.
    """
    pawn = _piece(PieceType.PAWN, Color.BLACK)
    board = {_pos("e7"): pawn}
    result = moves(pawn, _pos("e7"), board)
    assert _notations(result) == {"e6", "e5"}


def test_pawn_attacks_returns_diagonals_only():
    """
    Arrange: white pawn on e4.
    Act: attacks.
    Assert: only the two diagonal squares (d5, f5) — used for check detection,
    excluding the forward push square e5 which is not an attack square.
    """
    pawn = _piece(PieceType.PAWN)
    board = {_pos("e4"): pawn}
    result = attacks(pawn, _pos("e4"), board)
    assert _notations(result) == {"d5", "f5"}


def test_pawn_attacks_a_file_no_out_of_bounds():
    """
    Arrange: white pawn on a4, the leftmost file.
    Act: attacks.
    Assert: only b5 is returned; no index-wrapping or off-board square is generated.
    """
    pawn = _piece(PieceType.PAWN)
    board = {_pos("a4"): pawn}
    result = attacks(pawn, _pos("a4"), board)
    assert _notations(result) == {"b5"}


def test_pawn_attacks_black_faces_down():
    """
    Arrange: black pawn on e5.
    Act: attacks.
    Assert: black attacks the downward diagonals d4 and f4, not the squares above.
    """
    pawn = _piece(PieceType.PAWN, Color.BLACK)
    board = {_pos("e5"): pawn}
    result = attacks(pawn, _pos("e5"), board)
    assert _notations(result) == {"d4", "f4"}


def test_king_moves_from_e1():
    """
    Arrange: king on e1 (back rank center), empty board.
    Act: moves.
    Assert: exactly 5 destinations — back rank constrains two of the eight adjacents.
    """
    king = _piece(PieceType.KING)
    board = {_pos("e1"): king}
    result = moves(king, _pos("e1"), board)
    assert _notations(result) == {"d1", "f1", "d2", "e2", "f2"}


def test_knight_moves_from_g1(initial_state):
    """
    Arrange: knight on g1 in the initial position; e2 pawn is present.
    Act: moves.
    Assert: only f3 and h3 are reachable — e2 is occupied by a friendly pawn.
    """
    knight = initial_state.board[_pos("g1")]
    result = moves(knight, _pos("g1"), initial_state.board)
    assert _notations(result) == {"f3", "h3"}


def test_knight_moves_from_center():
    """
    Arrange: knight on d4 with no other pieces obstructing.
    Act: moves.
    Assert: a centrally-placed knight reaches all 8 L-shaped destinations.
    """
    knight = _piece(PieceType.KNIGHT)
    board = {_pos("d4"): knight}
    result = moves(knight, _pos("d4"), board)
    assert len(result) == 8


def test_knight_cannot_land_on_friendly():
    """
    Arrange: knight on d4, friendly rook on e6 — one of the knight's target squares.
    Act: moves.
    Assert: e6 is excluded; knights cannot capture own pieces.
    """
    knight = _piece(PieceType.KNIGHT)
    board = {_pos("d4"): knight, _pos("e6"): _piece(PieceType.ROOK)}
    result = moves(knight, _pos("d4"), board)
    assert "e6" not in _notations(result)


def test_knight_can_capture_enemy():
    """
    Arrange: knight on d4, enemy rook on e6 — one of the knight's target squares.
    Act: moves.
    Assert: e6 is included; the enemy piece is a valid capture target.
    """
    knight = _piece(PieceType.KNIGHT)
    board = {_pos("d4"): knight, _pos("e6"): _piece(PieceType.ROOK, Color.BLACK)}
    result = moves(knight, _pos("d4"), board)
    assert "e6" in _notations(result)


def test_bishop_moves_open_diagonal():
    """
    Arrange: white bishop on c1 with an otherwise empty board.
    Act: moves.
    Assert: the bishop slides to both ends of its diagonals, reaching a3 and h6.
    """
    bishop = _piece(PieceType.BISHOP)
    board = {_pos("c1"): bishop}
    result = moves(bishop, _pos("c1"), board)
    assert "a3" in _notations(result)
    assert "h6" in _notations(result)


def test_bishop_stops_at_enemy_and_captures():
    """
    Arrange: bishop on c1, black pawn blocking the diagonal at e3.
    Act: moves.
    Assert: e3 is included (capture), but f4 beyond it is not (ray stops at capture).
    """
    bishop = _piece(PieceType.BISHOP)
    board = {_pos("c1"): bishop, _pos("e3"): _piece(PieceType.PAWN, Color.BLACK)}
    result = moves(bishop, _pos("c1"), board)
    assert "e3" in _notations(result)
    assert "f4" not in _notations(result)


def test_bishop_blocked_by_friendly():
    """
    Arrange: bishop on c1 with a friendly pawn on d2, the first diagonal square.
    Act: moves.
    Assert: d2 is excluded; the ray stops before reaching a friendly piece.
    """
    bishop = _piece(PieceType.BISHOP)
    board = {_pos("c1"): bishop, _pos("d2"): _piece(PieceType.PAWN)}
    result = moves(bishop, _pos("c1"), board)
    assert "d2" not in _notations(result)


def test_rook_moves_clear_rank_and_file():
    """
    Arrange: rook on a1 with an empty board.
    Act: moves.
    Assert: the rook covers all seven squares on rank 1 and all seven on the a-file.
    """
    rook = _piece(PieceType.ROOK)
    board = {_pos("a1"): rook}
    result = moves(rook, _pos("a1"), board)
    assert "h1" in _notations(result)
    assert "a8" in _notations(result)


def test_rook_stops_at_enemy_and_captures():
    """
    Arrange: rook on a1, enemy pawn on a4 blocking the file.
    Act: moves.
    Assert: a4 is an included capture target, but a5 beyond it is cut off.
    """
    rook = _piece(PieceType.ROOK)
    board = {_pos("a1"): rook, _pos("a4"): _piece(PieceType.PAWN, Color.BLACK)}
    result = moves(rook, _pos("a1"), board)
    assert "a4" in _notations(result)
    assert "a5" not in _notations(result)


def test_rook_blocked_by_friendly():
    """
    Arrange: rook on a1 with a friendly pawn on a3 blocking the file.
    Act: moves.
    Assert: a3 is excluded; the ray stops before reaching a friendly piece.
    """
    rook = _piece(PieceType.ROOK)
    board = {_pos("a1"): rook, _pos("a3"): _piece(PieceType.PAWN)}
    result = moves(rook, _pos("a1"), board)
    assert "a3" not in _notations(result)


def test_queen_moves_combines_bishop_and_rook():
    """
    Arrange: queen on d4 with an empty board.
    Act: moves.
    Assert: the queen's reach is exactly the union of bishop and rook destinations
    from the same square — no more, no less.
    """
    board = {_pos("d4"): _piece(PieceType.QUEEN)}
    q_moves = _notations(moves(_piece(PieceType.QUEEN), _pos("d4"), board))
    r_moves = _notations(moves(_piece(PieceType.ROOK), _pos("d4"), board))
    b_moves = _notations(moves(_piece(PieceType.BISHOP), _pos("d4"), board))
    assert q_moves == r_moves | b_moves


def test_king_moves_from_center():
    """
    Arrange: king on e4, surrounded by empty squares in all directions.
    Act: moves.
    Assert: a king in the centre can reach all 8 adjacent squares.
    """
    king = _piece(PieceType.KING)
    board = {_pos("e4"): king}
    result = moves(king, _pos("e4"), board)
    assert len(result) == 8


def test_king_moves_from_corner():
    """
    Arrange: king on a1 (corner), empty board.
    Act: moves.
    Assert: only 3 destinations (b1, a2, b2) — the board edge removes 5 adjacents.
    """
    king = _piece(PieceType.KING)
    board = {_pos("a1"): king}
    result = moves(king, _pos("a1"), board)
    assert _notations(result) == {"b1", "a2", "b2"}


def test_king_cannot_land_on_friendly():
    """
    Arrange: king on e1 with a friendly pawn on d2, one of the adjacent squares.
    Act: moves.
    Assert: d2 is excluded; the king cannot displace its own pieces.
    """
    king = _piece(PieceType.KING)
    board = {_pos("e1"): king, _pos("d2"): _piece(PieceType.PAWN)}
    result = moves(king, _pos("e1"), board)
    assert "d2" not in _notations(result)


def test_knight_moves_from_corner():
    """
    Arrange: knight on a1 (corner), empty board.
    Act: moves.
    Assert: only b3 and c2 are reachable — the 6 other L-shapes leave the board.
    """
    knight = _piece(PieceType.KNIGHT)
    board = {_pos("a1"): knight}
    result = moves(knight, _pos("a1"), board)
    assert _notations(result) == {"b3", "c2"}


def test_king_can_capture_enemy():
    """
    Arrange: white king on e1 with a lone black pawn on d2.
    Act: moves.
    Assert: d2 is included — the king can step onto an adjacent enemy square.
    """
    king = _piece(PieceType.KING)
    board = {_pos("e1"): king, _pos("d2"): _piece(PieceType.PAWN, Color.BLACK)}
    result = moves(king, _pos("e1"), board)
    assert "d2" in _notations(result)


def test_pawn_at_h_file_attacks_only_left_diagonal():
    """
    Arrange: white pawn on h4, the rightmost file.
    Act: attacks.
    Assert: only g5 is returned; no off-board square to the right is generated.
    """
    pawn = _piece(PieceType.PAWN)
    board = {_pos("h4"): pawn}
    result = attacks(pawn, _pos("h4"), board)
    assert _notations(result) == {"g5"}


def test_bishop_full_count_from_center():
    """
    Arrange: white bishop on d4 with an otherwise empty board.
    Act: moves.
    Assert: from d4, all four diagonals yield exactly 13 reachable squares.
    """
    bishop = _piece(PieceType.BISHOP)
    board = {_pos("d4"): bishop}
    result = moves(bishop, _pos("d4"), board)
    assert len(result) == 13


# attacks


def test_attacks_non_pawn_delegates_to_moves():
    """
    Arrange: white rook on a1.
    Act: attacks.
    Assert: result equals moves() — non-pawn attack squares are identical to
    reachable move squares.
    """
    rook = _piece(PieceType.ROOK)
    board = {_pos("a1"): rook}
    assert _notations(attacks(rook, _pos("a1"), board)) == _notations(
        moves(rook, _pos("a1"), board)
    )


# is_attacked


def test_is_attacked_by_rook_along_file():
    """
    Arrange: black rook on e8; target square e1; e-file is otherwise empty.
    Act: is_attacked(e1, BLACK, board).
    Assert: True — the rook's open ray reaches e1.
    """
    board = Board({_pos("e8"): _piece(PieceType.ROOK, Color.BLACK)})
    assert is_attacked(_pos("e1"), Color.BLACK, board) is True


def test_is_attacked_by_pawn_diagonally():
    """
    Arrange: black pawn on d5; target square e4.
    Act: is_attacked(e4, BLACK, board).
    Assert: True — a black pawn on d5 attacks e4 diagonally downward.
    """
    board = Board({_pos("d5"): _piece(PieceType.PAWN, Color.BLACK)})
    assert is_attacked(_pos("e4"), Color.BLACK, board) is True


def test_is_not_attacked_when_blocked():
    """
    Arrange: black rook on e8; white pawn on e4 blocking the ray before e1.
    Act: is_attacked(e1, BLACK, board).
    Assert: False — the rook cannot see through the blocking pawn.
    """
    board = Board(
        {
            _pos("e8"): _piece(PieceType.ROOK, Color.BLACK),
            _pos("e4"): _piece(PieceType.PAWN, Color.WHITE),
        }
    )
    assert is_attacked(_pos("e1"), Color.BLACK, board) is False


def test_is_attacked_by_knight_cannot_be_blocked():
    """
    Arrange: black knight on f3; target square e1; white pawn on e2 in between.
    Act: is_attacked(e1, BLACK, board).
    Assert: True — a knight's leap clears all intervening pieces.
    """
    board = Board(
        {
            _pos("f3"): _piece(PieceType.KNIGHT, Color.BLACK),
            _pos("e2"): _piece(PieceType.PAWN, Color.WHITE),
        }
    )
    assert is_attacked(_pos("e1"), Color.BLACK, board) is True


# is_in_check


def test_is_in_check_king_under_rook_attack():
    """
    Arrange: white king on e1, black rook on e8 aiming down the open e-file.
    Act: is_in_check(WHITE, board).
    Assert: True — the rook's ray reaches the white king.
    """
    board = Board(
        {
            _pos("e1"): _piece(PieceType.KING, Color.WHITE),
            _pos("e8"): _piece(PieceType.ROOK, Color.BLACK),
            _pos("a8"): _piece(PieceType.KING, Color.BLACK),
        }
    )
    assert is_in_check(Color.WHITE, board) is True


def test_is_not_in_check_at_game_start(initial_state):
    """
    Arrange: standard opening position — both kings fully shielded by their pawns.
    Act: is_in_check(WHITE, initial board).
    Assert: False — neither king is under attack at the start.
    """
    assert is_in_check(Color.WHITE, initial_state.board) is False


# pawn boundary safety


def test_white_pawn_at_back_rank_has_no_moves():
    """
    Arrange: white pawn sitting on rank 8 (should have been promoted).
    Act: moves.
    Assert: empty — no forward push is generated and no ValidationError is raised.
    """
    pawn = _piece(PieceType.PAWN)
    board = {_pos("e8"): pawn}
    result = moves(pawn, _pos("e8"), board)
    assert result == []


def test_black_pawn_at_back_rank_has_no_moves():
    """
    Arrange: black pawn sitting on rank 1 (should have been promoted).
    Act: moves.
    Assert: empty — no forward push is generated and no ValidationError is raised.
    """
    pawn = _piece(PieceType.PAWN, Color.BLACK)
    board = {_pos("e1"): pawn}
    result = moves(pawn, _pos("e1"), board)
    assert result == []


def test_white_pawn_one_step_from_back_rank():
    """
    Arrange: white pawn on rank 7, one step from the back rank, path clear.
    Act: moves.
    Assert: only e8 — the single forward push; no two-step (not on starting rank).
    """
    pawn = _piece(PieceType.PAWN)
    board = {_pos("e7"): pawn}
    result = moves(pawn, _pos("e7"), board)
    assert _notations(result) == {"e8"}


def test_black_pawn_one_step_from_back_rank():
    """
    Arrange: black pawn on rank 2, one step from the back rank, path clear.
    Act: moves.
    Assert: only e1 — the single forward push; no two-step (not on starting rank).
    """
    pawn = _piece(PieceType.PAWN, Color.BLACK)
    board = {_pos("e2"): pawn}
    result = moves(pawn, _pos("e2"), board)
    assert _notations(result) == {"e1"}


def test_white_pawn_at_back_rank_has_no_attacks():
    """
    Arrange: white pawn on rank 8.
    Act: attacks.
    Assert: empty — no diagonal threat squares exist above rank 8.
    """
    pawn = _piece(PieceType.PAWN)
    board = {_pos("e8"): pawn}
    assert attacks(pawn, _pos("e8"), board) == []


def test_black_pawn_at_back_rank_has_no_attacks():
    """
    Arrange: black pawn on rank 1.
    Act: attacks.
    Assert: empty — no diagonal threat squares exist below rank 1.
    """
    pawn = _piece(PieceType.PAWN, Color.BLACK)
    board = {_pos("e1"): pawn}
    assert attacks(pawn, _pos("e1"), board) == []
