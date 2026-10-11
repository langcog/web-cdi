from django.test import SimpleTestCase, tag

from cdi_forms.templatetags.sanitize import sanitize_richtext


@tag("sanitize")
class SanitizeRichtextTest(SimpleTestCase):
    """The study waiver / end-message fields are authored by researchers and
    rendered into parents' browsers. sanitize_richtext is the control that
    keeps stored content from injecting script — these tests lock that in so a
    later refactor can't silently weaken it."""

    def render(self, value):
        return str(sanitize_richtext(value))

    # --- formatting is preserved -------------------------------------------
    def test_markdown_bold_and_links(self):
        out = self.render("Please **consent**. See [details](https://x.org).")
        self.assertIn("<strong>consent</strong>", out)
        self.assertIn('href="https://x.org"', out)

    def test_markdown_lists(self):
        out = self.render("- one\n- two")
        self.assertIn("<ul>", out)
        self.assertIn("<li>one</li>", out)

    def test_legacy_html_passes_through(self):
        # content stored by the old rich-text editor is HTML, not Markdown
        out = self.render("<p>Old <strong>editor</strong> content</p>")
        self.assertIn("<strong>editor</strong>", out)
        self.assertIn("Old", out)

    def test_mailto_and_http_links_allowed(self):
        self.assertIn("mailto:a@b.org", self.render("[mail](mailto:a@b.org)"))
        self.assertIn("http://x.org", self.render("[x](http://x.org)"))

    # --- dangerous content is stripped -------------------------------------
    def test_script_tag_removed(self):
        out = self.render("hello <script>alert(1)</script>")
        self.assertNotIn("<script", out)

    def test_event_handler_attribute_removed(self):
        out = self.render('<p onclick="steal()">hi</p>')
        self.assertNotIn("onclick", out)

    def test_img_onerror_removed(self):
        out = self.render('<img src="x" onerror="alert(1)">')
        self.assertNotIn("onerror", out)

    def test_javascript_protocol_link_removed(self):
        out = self.render("[click](javascript:alert(1))")
        self.assertNotIn("javascript:", out)

    def test_iframe_and_style_removed(self):
        out = self.render('<iframe src="evil"></iframe><style>x{}</style>ok')
        self.assertNotIn("<iframe", out)
        self.assertNotIn("<style", out)
        self.assertIn("ok", out)

    # --- edge cases --------------------------------------------------------
    def test_empty_and_none(self):
        self.assertEqual(self.render(""), "")
        self.assertEqual(str(sanitize_richtext(None)), "")
