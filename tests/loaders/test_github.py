import pytest

from kabigon.core.exception import InvalidURLError
from kabigon.loaders.github import check_github_url
from kabigon.loaders.github import extract_main_html
from kabigon.loaders.github import to_raw_github_url


def test_extract_main_html_prefers_main() -> None:
    html = """
    <html>
      <body>
        <header>Top Nav</header>
        <main>
          <h1>Repo Title</h1>
          <p>Hello world</p>
        </main>
        <footer>Footer</footer>
      </body>
    </html>
    """
    extracted = extract_main_html(html)
    assert "Repo Title" in extracted
    assert "Hello world" in extracted
    assert "Top Nav" not in extracted
    assert "Footer" not in extracted


def test_extract_main_html_falls_back_to_article() -> None:
    html = """
    <html>
      <body>
        <article><p>Article body</p></article>
      </body>
    </html>
    """
    extracted = extract_main_html(html)
    assert "Article body" in extracted


def test_extract_main_html_falls_back_to_full_html() -> None:
    html = "<html><body><div>Only body</div></body></html>"
    extracted = extract_main_html(html)
    assert extracted == html


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
