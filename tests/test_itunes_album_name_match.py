"""Tests for iTunesWorker album name matching with edition-guard."""
from __future__ import annotations
from unittest.mock import MagicMock, patch
from core.itunes_worker import iTunesWorker


def _worker():
    w = iTunesWorker.__new__(iTunesWorker)
    w.name_similarity_threshold = 0.80
    return w


# ── _name_matches — edition markers must reject ─────────────────────────────

def test_lemonade_vs_karina_special_version_rejected():
    assert _worker()._name_matches('LEMONADE', 'LEMONADE (KARINA Special Version)') is False


def test_1989_vs_taylors_version_rejected():
    assert _worker()._name_matches('1989', '1989 (Taylor\'s Version)') is False


def test_ok_computer_vs_oknotok_rejected():
    assert _worker()._name_matches('OK Computer', 'OK Computer (OKNOTOK 1997 2017)') is False


def test_thriller_vs_expanded_edition_rejected():
    assert _worker()._name_matches('Thriller', 'Thriller (Expanded Edition)') is False


# ── _name_matches — allowed suffixes must accept ────────────────────────────

def test_abbey_road_vs_remastered_accepted():
    assert _worker()._name_matches('Abbey Road', 'Abbey Road (Remastered 2019)') is True


def test_abbey_road_vs_bare_year_accepted():
    assert _worker()._name_matches('Abbey Road', 'Abbey Road (2019)') is True


def test_title_vs_explicit_accepted():
    assert _worker()._name_matches('abbey road', 'abbey road (explicit)') is True


def test_exact_match_accepted():
    assert _worker()._name_matches('LEMONADE', 'LEMONADE') is True


# ── _has_duplicate_itunes_id ─────────────────────────────────────────────────

def test_no_conflict_returns_none():
    w = _worker()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    w.db = MagicMock()
    w.db._get_connection.return_value = mock_conn

    result = w._has_duplicate_itunes_id(db_id=42, source_id='999')
    assert result is None
    mock_cursor.execute.assert_called_once_with(
        "SELECT id, title FROM albums WHERE itunes_album_id = ? AND id != ?",
        ('999', 42),
    )


def test_conflict_returns_row():
    w = _worker()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = ('other-id', 'LEMONADE (KARINA Special Version)')
    w.db = MagicMock()
    w.db._get_connection.return_value = mock_conn

    result = w._has_duplicate_itunes_id(db_id=42, source_id='999')
    assert result == ('other-id', 'LEMONADE (KARINA Special Version)')
