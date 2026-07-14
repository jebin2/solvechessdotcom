from solvechessdotcom.video import _format_solution_text


def test_format_solution_text():
    solution = {
        'move1': {'white': 'e6f7', 'black': 'h7h6'},
        'move2': {'white': 'e1g1', 'white_castle_move': 'h1f1', 'black': None},
    }
    text = _format_solution_text(solution)
    lines = text.split('\n')
    assert lines[0] == "1.  e6-f7     h7-h6"
    assert lines[1] == "2.  e1-g1     h1-f1"


def test_format_solution_skips_empty_moves():
    solution = {'move1': {'white': '', 'black': None}}
    assert _format_solution_text(solution) == ''
