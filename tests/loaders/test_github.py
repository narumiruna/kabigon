import pytest

from kabigon.core.exception import InvalidURLError
from kabigon.loaders.github import check_github_url
from kabigon.loaders.github import to_raw_github_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://github.com/anthropics/claude-code/blob/main/plugins/ralph-wiggum/README.md",
            "https://raw.githubusercontent.com/anthropics/claude-code/main/plugins/ralph-wiggum/README.md",
        ),
        (
            "https://raw.githubusercontent.com/anthropics/claude-code/main/plugins/ralph-wiggum/README.md",
            "https://raw.githubusercontent.com/anthropics/claude-code/main/plugins/ralph-wiggum/README.md",
        ),
    ],
)
def test_to_raw_github_url(url: str, expected: str) -> None:
    assert to_raw_github_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com",
        "https://github.com/anthropics/claude-code",
        "https://github.com/anthropics/claude-code/blob/main",
    ],
)
def test_to_raw_github_url_error(url: str) -> None:
    with pytest.raises(InvalidURLError):
        to_raw_github_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/anthropics/claude-code/blob/main/plugins/ralph-wiggum/README.md",
        "https://raw.githubusercontent.com/anthropics/claude-code/main/plugins/ralph-wiggum/README.md",
    ],
)
def test_check_github_url(url: str) -> None:
    check_github_url(url)  # should not raise


def test_check_github_url_error() -> None:
    with pytest.raises(InvalidURLError, match="URL is not a GitHub URL"):
        check_github_url("https://example.com/x")
