import pytest

from kabigon.loaders.html_extractors import extract_first_tag_subtree
from kabigon.loaders.utils import html_to_markdown


@pytest.mark.parametrize(
    "ignored_html",
    [
        '<nav><div><a href="/">Navigation</a></div></nav>',
        "<svg><g><path /></g></svg>",
        "<nav><div><nav><span>Nested navigation</span></nav></div></nav>",
    ],
)
def test_ignored_descendants_do_not_extend_capture(ignored_html: str) -> None:
    html = f"<main>{ignored_html}<p>Article body</p></main><aside>Outside content</aside>"

    extracted = extract_first_tag_subtree(html, ("main",), ignored_tags={"nav", "svg"})

    assert extracted == "<main><p>Article body</p></main>"
    assert html_to_markdown(extracted) == "Article body"


def test_ignored_void_tag_does_not_hide_following_content() -> None:
    html = '<main><img src="example.png"><p>Article body</p></main><aside>Outside</aside>'

    extracted = extract_first_tag_subtree(html, ("main",), ignored_tags={"img"})

    assert extracted == "<main><p>Article body</p></main>"


@pytest.mark.parametrize("text", ["&lt;widget&gt;", "&amp;lt;tag&amp;gt;", "one &amp; two", "x &lt; y"])
def test_reconstructed_html_preserves_escaped_text(text: str) -> None:
    html = f"<main><pre><code>{text}</code></pre></main>"

    extracted = extract_first_tag_subtree(html, ("main",))

    assert html_to_markdown(extracted) == html_to_markdown(html)
