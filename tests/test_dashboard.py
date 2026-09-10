from __future__ import annotations

from pathlib import Path

from nhl_pipeline import dashboard


def test_dashboard_prefers_mp4_when_available(tmp_path, monkeypatch):
    gif_path = tmp_path / "race.gif"
    mp4_path = tmp_path / "race.mp4"
    gif_path.write_bytes(b"gif")
    mp4_path.write_bytes(b"mp4")
    monkeypatch.setattr(dashboard, "OUTPUT_DIR", Path(tmp_path))

    assert dashboard._resolve_media_path("race.gif") == mp4_path


def test_dashboard_falls_back_to_gif_without_mp4(tmp_path, monkeypatch):
    gif_path = tmp_path / "race.gif"
    gif_path.write_bytes(b"gif")
    monkeypatch.setattr(dashboard, "OUTPUT_DIR", Path(tmp_path))

    assert dashboard._resolve_media_path("race.gif") == gif_path
