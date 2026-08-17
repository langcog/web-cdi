import bleach
import markdown
from django import template
from django.utils.safestring import mark_safe
from markdown.extensions.legacy_em import LegacyEmExtension

register = template.Library()

# Safe subset for researcher-authored rich text (study waiver / end message).
# These fields are authored as Markdown and rendered into parents' browsers,
# so the produced HTML is sanitized on the way out — dropping <script>, on*
# handlers, javascript: URLs, style/embed/iframe, etc. Content stored earlier
# as raw HTML (from the previous rich-text editor) passes through Markdown
# unchanged and is sanitized the same way.
ALLOWED_TAGS = [
    "a", "abbr", "b", "blockquote", "br", "code", "div", "em", "h1", "h2",
    "h3", "h4", "h5", "h6", "hr", "i", "img", "li", "ol", "p", "pre", "s",
    "span", "strong", "sub", "sup", "u", "ul",
]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
    "*": ["class"],
}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


@register.filter
def sanitize_richtext(value):
    if not value:
        return ""
    html = markdown.markdown(str(value), extensions=[LegacyEmExtension()])
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    return mark_safe(cleaned)
