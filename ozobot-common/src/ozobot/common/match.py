import re


def match_with_wildcard(pattern: str, string: str) -> bool:
    r"""
    Matches the given string against an start and end anchored pattern containing wildcard `*` characters.

    All the other characters are interpreted literaly (does not match regexes!).
    Example:
        "abc*" matches "abcANYTHING", but not "ANYTHINGabc" nor "abc*""
        "abc[0-9]*" matches "abc[0-9]ANYTHING", not "abc1234"
    """

    pattern = re.escape(pattern)
    pattern = pattern.replace(r"\*", ".*")
    pattern = f"^{pattern}$"

    return re.match(pattern, string) is not None
