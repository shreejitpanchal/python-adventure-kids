from app.engine.validator import validate_ast_contains, validate_output


def test_exact_match():
    assert validate_output("Hello!\n", "Hello!") is True


def test_mismatch():
    assert validate_output("Hello\n", "Hello!") is False


def test_ignores_surrounding_whitespace_only():
    assert validate_output("  5  \n", "5") is True
    assert validate_output("5 6", "5") is False


def test_input_placeholder_is_substituted_when_input_value_given():
    assert validate_output("Hello Sam\n", "Hello {input}", input_value="Sam") is True
    assert validate_output("Hello Priya\n", "Hello {input}", input_value="Sam") is False


def test_input_placeholder_left_alone_without_input_value():
    assert validate_output("Hello {input}", "Hello {input}") is True


def test_expected_output_without_placeholder_ignores_input_value():
    assert validate_output("5\n", "5", input_value="Sam") is True


def test_pattern_matches_any_alternative():
    pattern = r"^(You win!|You lose!|It's a tie!)$"
    assert validate_output("You win!\n", expected_output_pattern=pattern) is True
    assert validate_output("It's a tie!\n", expected_output_pattern=pattern) is True
    assert validate_output("Something else\n", expected_output_pattern=pattern) is False


def test_pattern_takes_priority_over_expected_output():
    assert validate_output("42\n", expected_output="99", expected_output_pattern=r"^\d+$") is True


# -- validate_ast_contains ----------------------------------------------------
def test_ast_contains_empty_patterns_always_passes():
    assert validate_ast_contains("anything at all !!!", []) is True


def test_ast_contains_syntax_error_fails():
    assert validate_ast_contains("def broken(:", ["print"]) is False


def test_ast_contains_keyword_for_loop():
    assert validate_ast_contains("for i in range(5):\n    print(i)", ["for"]) is True
    assert validate_ast_contains("print('no loop here')", ["for"]) is False


def test_ast_contains_keyword_while_if_def_return():
    assert validate_ast_contains("while True:\n    break", ["while"]) is True
    assert validate_ast_contains("if x > 1:\n    pass", ["if"]) is True
    assert validate_ast_contains("def f():\n    return 1", ["def", "return"]) is True


def test_ast_contains_keyword_global():
    code = "x = 0\ndef bump():\n    global x\n    x += 1"
    assert validate_ast_contains(code, ["global"]) is True
    assert validate_ast_contains("x = 0\nx += 1", ["global"]) is False


def test_ast_contains_bare_identifier_as_a_call():
    assert validate_ast_contains('print("hi")', ["print"]) is True
    assert validate_ast_contains('x = int("5")', ["int"]) is True
    assert validate_ast_contains("y = 5", ["print"]) is False


def test_ast_contains_dotted_attribute_as_a_call():
    code = 'inventory = ["map"]\ninventory.append("sword")\nprint(inventory)'
    assert validate_ast_contains(code, ["inventory.append"]) is True


def test_ast_contains_dotted_attribute_as_a_plain_assignment():
    code = "ball.speed_x = 4\nball.speed_y = 4"
    assert validate_ast_contains(code, ["ball.speed_x", "ball.speed_y"]) is True


def test_ast_contains_bare_identifier_matches_trailing_part_of_dotted_call():
    # canvas.forward(100) satisfies a bare "forward" pattern, matching how
    # the spec's own Creative Arts examples list ast_contains: ["forward"]
    # rather than the fully dotted "canvas.forward".
    assert validate_ast_contains("canvas.forward(100)\ncanvas.turn_right(90)", ["forward", "turn_right"]) is True


def test_ast_contains_requires_every_pattern_and_semantics():
    code = "for i in range(3):\n    print(i)"
    assert validate_ast_contains(code, ["for", "print"]) is True
    assert validate_ast_contains(code, ["for", "print", "while"]) is False


def test_ast_contains_does_not_match_unrelated_object_with_same_method_name():
    # "inventory.append" must not be satisfied by some other object's
    # .append() -- the base name has to match too.
    code = "scores = []\nscores.append(5)"
    assert validate_ast_contains(code, ["inventory.append"]) is False


def test_ast_contains_code_crackers_style_fix():
    code = 'user_score = "150"\nbonus_points = 50\ntotal_score = int(user_score) + bonus_points\nprint(total_score)'
    assert validate_ast_contains(code, ["int", "print"]) is True
