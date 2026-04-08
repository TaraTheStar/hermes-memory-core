from domain.core.prompt_sanitizer import sanitize_field


class TestSanitizeField:
    def test_basic_wrapping(self):
        result = sanitize_field("hello", "goal")
        assert result == "<goal>hello</goal>"

    def test_none_input(self):
        result = sanitize_field(None, "goal")
        assert result == "<goal></goal>"

    def test_numeric_input_coerced(self):
        result = sanitize_field(42, "n")
        assert result == "<n>42</n>"

    def test_truncation_at_max_length(self):
        text = "a" * 2001
        result = sanitize_field(text, "data")
        assert result.startswith("<data>" + "a" * 2000)
        assert "... [truncated]" in result
        assert result.endswith("</data>")

    def test_exact_max_length_not_truncated(self):
        text = "a" * 2000
        result = sanitize_field(text, "data")
        assert "truncated" not in result

    def test_custom_max_length(self):
        text = "a" * 15
        result = sanitize_field(text, "x", max_length=10)
        assert "... [truncated]" in result

    def test_closing_tag_escaped(self):
        result = sanitize_field("before</goal>after", "goal")
        assert "</goal>" not in result.split(">", 1)[1].rsplit("<", 1)[0]
        assert r"<\/goal>" in result

    def test_escape_uses_dynamic_tag_name(self):
        # </foo> should NOT be escaped when tag is "goal"
        result = sanitize_field("has </foo> inside", "goal")
        assert "</foo>" in result

    def test_empty_string(self):
        result = sanitize_field("", "tag")
        assert result == "<tag></tag>"
