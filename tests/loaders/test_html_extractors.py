import pytest

from kabigon.loaders.html_extractors import extract_first_tag_subtree
from kabigon.loaders.utils import html_to_markdown


@pytest.mark.parametrize(
    "ignored_html",
    [
        '<nav><div><a href="/">Navigation</a></div></nav>',
        "<svg><g><path /></g></svg>",
        "<nav><div><nav><span>Nested navigation</span></nav></div></nav>",
        "<nav><ul><li>One<li>Two</ul></nav>",
        "<nav><p>One<p>Two</nav>",
        "<nav><table><tr><td>One<td>Two</table></nav>",
        "<nav><div>Unclosed descendant</nav>",
        "<nav>Navigation</span>Still navigation</nav>",
        "<nav><img src='example.png'><br>Navigation</nav>",
        "<nav /><svg />",
    ],
)
def test_ignored_descendants_do_not_extend_capture(ignored_html: str) -> None:
    html = f"<main>{ignored_html}<p>Article body</p></main><aside>Outside content</aside>"

    extracted = extract_first_tag_subtree(html, ("main",), ignored_tags={"nav", "svg"})

    assert extracted == "<main><p>Article body</p></main>"
    assert html_to_markdown(extracted) == "Article body"


@pytest.mark.parametrize("ignored_html", ["<nav>Navigation", "<nav><div>Navigation", "<svg><g>Drawing"])
def test_capture_root_closes_unclosed_ignored_subtrees(ignored_html: str) -> None:
    html = f"<main><p>Article body</p>{ignored_html}</main><aside>Outside content</aside>"

    extracted = extract_first_tag_subtree(html, ("main",), ignored_tags={"nav", "svg"})

    assert extracted == "<main><p>Article body</p></main>"


def test_nested_capture_root_inside_ignored_subtree_does_not_end_capture() -> None:
    html = (
        "<article><nav><article>Ignored article</article></nav><p>Article body</p></article>"
        "<aside>Outside content</aside>"
    )

    extracted = extract_first_tag_subtree(html, ("article",), ignored_tags={"nav"})

    assert extracted == "<article><p>Article body</p></article>"


def test_ignored_void_tag_does_not_hide_following_content() -> None:
    html = '<main><img src="example.png"><p>Article body</p></main><aside>Outside</aside>'

    extracted = extract_first_tag_subtree(html, ("main",), ignored_tags={"img"})

    assert extracted == "<main><p>Article body</p></main>"


@pytest.mark.parametrize("text", ["&lt;widget&gt;", "&amp;lt;tag&amp;gt;", "one &amp; two", "x &lt; y"])
def test_reconstructed_html_preserves_escaped_text(text: str) -> None:
    html = f"<main><pre><code>{text}</code></pre></main>"

    extracted = extract_first_tag_subtree(html, ("main",))

    assert html_to_markdown(extracted) == html_to_markdown(html)
