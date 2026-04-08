"""Tests for YouTubeContentSkill — URL parsing, validation, and transcript handling."""
import os
import subprocess
import pytest
from unittest.mock import patch, MagicMock
from infrastructure.youtube_content import YouTubeContentSkill


@pytest.fixture
def skill():
    return YouTubeContentSkill()


class TestExtractVideoId:
    def test_standard_url(self, skill):
        assert skill._extract_video_id("https://www.youtube.com/watch?v=oYlcUbLAFmw") == "oYlcUbLAFmw"

    def test_short_url(self, skill):
        assert skill._extract_video_id("https://youtu.be/oYlcUbLAFmw") == "oYlcUbLAFmw"

    def test_url_with_extra_params(self, skill):
        assert skill._extract_video_id("https://www.youtube.com/watch?v=oYlcUbLAFmw&t=120") == "oYlcUbLAFmw"

    def test_embed_url(self, skill):
        assert skill._extract_video_id("https://www.youtube.com/embed/oYlcUbLAFmw") == "oYlcUbLAFmw"

    def test_invalid_url(self, skill):
        assert skill._extract_video_id("https://example.com/page") is None

    def test_empty_string(self, skill):
        assert skill._extract_video_id("") is None


class TestGetTranscriptValidation:
    def test_invalid_url_returns_error(self, skill):
        result = skill.get_transcript("not-a-youtube-url")
        assert result["status"] == "error"
        assert "Invalid YouTube URL" in result["error"]

    def test_invalid_lang_code_returns_error(self, skill):
        result = skill.get_transcript("https://www.youtube.com/watch?v=oYlcUbLAFmw", lang="not_valid!")
        assert result["status"] == "error"
        assert "Invalid language code" in result["error"]

    def test_valid_lang_codes(self, skill):
        for lang in ["en", "pt-BR", "zh-TW", "fra"]:
            assert skill._LANG_PATTERN.match(lang), f"Expected {lang} to be valid"

    def test_invalid_lang_codes(self, skill):
        for lang in ["en_US", "x", "a-b-c-d-e", "123", "en US"]:
            assert not skill._LANG_PATTERN.match(lang), f"Expected {lang} to be invalid"


class TestGetTranscriptExecution:
    def test_success_path(self, skill, tmp_path):
        """Should parse SRT content into plain text."""
        srt_content = "1\n00:00:01,000 --> 00:00:02,000\nHello world\n\n2\n00:00:02,000 --> 00:00:03,000\nGoodbye\n"

        def fake_run(cmd, **kwargs):
            # Write a fake SRT file in the temp dir (extracted from -o arg)
            output_template = cmd[cmd.index("-o") + 1]
            srt_path = output_template + ".en.srt"
            os.makedirs(os.path.dirname(srt_path), exist_ok=True)
            with open(srt_path, "w") as f:
                f.write(srt_content)
            return MagicMock(returncode=0)

        with patch("infrastructure.youtube_content.subprocess.run", side_effect=fake_run):
            result = skill.get_transcript("https://www.youtube.com/watch?v=oYlcUbLAFmw")

        assert result["status"] == "success"
        assert result["video_id"] == "oYlcUbLAFmw"
        assert "Hello world" in result["full_text"]
        assert "Goodbye" in result["full_text"]
        # SRT metadata should be stripped
        assert "-->" not in result["full_text"]

    def test_no_srt_file_found(self, skill):
        """Should return error when yt-dlp produces no .srt file."""
        with patch("infrastructure.youtube_content.subprocess.run"):
            result = skill.get_transcript("https://www.youtube.com/watch?v=oYlcUbLAFmw")

        assert result["status"] == "error"
        assert "Could not find" in result["error"]

    def test_subprocess_failure(self, skill):
        """Should return error when yt-dlp fails."""
        with patch("infrastructure.youtube_content.subprocess.run",
                    side_effect=subprocess.CalledProcessError(1, "yt-dlp", stderr="download failed")):
            result = skill.get_transcript("https://www.youtube.com/watch?v=oYlcUbLAFmw")

        assert result["status"] == "error"
        assert "yt-dlp failed" in result["error"]
        assert result["video_id"] == "oYlcUbLAFmw"

    def test_generic_exception(self, skill):
        """Should return error for unexpected exceptions."""
        with patch("infrastructure.youtube_content.subprocess.run",
                    side_effect=OSError("disk full")):
            result = skill.get_transcript("https://www.youtube.com/watch?v=oYlcUbLAFmw")

        assert result["status"] == "error"
        assert "disk full" in result["error"]

    def test_temp_dir_cleaned_up_on_success(self, skill):
        """Temp directory should be cleaned up even on success."""
        created_dirs = []

        original_mkdtemp = __import__("tempfile").mkdtemp
        def tracking_mkdtemp(**kwargs):
            d = original_mkdtemp(**kwargs)
            created_dirs.append(d)
            return d

        with patch("infrastructure.youtube_content.tempfile.mkdtemp", side_effect=tracking_mkdtemp):
            with patch("infrastructure.youtube_content.subprocess.run"):
                skill.get_transcript("https://www.youtube.com/watch?v=oYlcUbLAFmw")

        assert len(created_dirs) == 1
        assert not os.path.exists(created_dirs[0])
