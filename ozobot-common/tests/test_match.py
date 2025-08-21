import pytest
from ozobot.common.match import match_with_wildcard


@pytest.mark.parametrize(
    ("pattern", "string", "expected_match"),
    (
        ("abc*", "abcdef", True),
        ("abc*", "abc", True),
        ("abc", "abc", True),
        ("abc", "abcdef", False),
        ("def*", "abcdef", False),
        ("abc*xyz", "abcdefxyz", True),
        ("abc*ghi*xyz", "abcdefghixyz", True),
        ("*def", "abcdef", True),
    ),
    ids=lambda x: repr(x),
)
def test_match_with_wildcard(pattern: str, string: str, expected_match: bool) -> None:
    assert match_with_wildcard(pattern, string) == expected_match
