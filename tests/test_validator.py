from app.engine.validator import validate_output


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
