from app.sandbox.errors import extract_error_line_number, translate_error

SYNTAX_STDERR = '''  File "<your code>", line 1
    print("Hello!"
         ^
SyntaxError: '(' was never closed
'''

NAME_ERROR_STDERR = '''Traceback (most recent call last):
  File "<your code>", line 1, in <module>
    print(mystery)
NameError: name 'mystery' is not defined
'''


def test_translate_syntax_error():
    friendly, hint = translate_error(SYNTAX_STDERR)
    assert "isn't quite right" in friendly
    assert hint


def test_translate_name_error():
    friendly, hint = translate_error(NAME_ERROR_STDERR)
    assert "doesn't recognize" in friendly


def test_translate_unknown_error_falls_back_to_default():
    friendly, hint = translate_error("SomeWeirdError: whatever")
    assert friendly
    assert hint


def test_translate_eof_error():
    friendly, hint = translate_error("EOFError: EOF when reading a line")
    assert "waiting for an answer" in friendly
    assert hint


def test_extract_error_line_number():
    assert extract_error_line_number(SYNTAX_STDERR) == 1
    assert extract_error_line_number(NAME_ERROR_STDERR) == 1
    assert extract_error_line_number("no file reference here") is None
