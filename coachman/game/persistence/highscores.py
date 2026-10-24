"""Recordes -- padrão **Repository** (Martin Fowler, *Patterns of Enterprise
Application Architecture*, 2002; https://martinfowler.com/eaaCatalog/repository.html).

O jogo só fala com a interface ``HighScoreRepository`` ("me dê os 10
melhores", "guarde este recorde"). Onde os dados moram é detalhe de
implementação, escolhido em tempo de execução por ``create_repository``:

* ``SqliteHighScoreRepository`` -- no computador, mantém o SQLite da versão
  original do projeto (arquivo ``~/.coachman/scores.db``);
* ``BrowserHighScoreRepository`` -- no navegador, usa o ``localStorage``
  (cada jogador vê os próprios recordes, nada é enviado para servidor);
* ``InMemoryHighScoreRepository`` -- nos testes e como plano B.
"""
from __future__ import annotations

import json
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

MAX_ENTRIES = 10


@dataclass(frozen=True)
class ScoreEntry:
    initials: str
    score: int
    level: int = 1
    day: str = ""

    @staticmethod
    def new(initials: str, score: int, level: int) -> "ScoreEntry":
        clean = "".join(ch for ch in initials.upper() if ch.isalnum())[:3] or "???"
        return ScoreEntry(clean, max(0, int(score)), max(1, int(level)), date.today().isoformat())


class HighScoreRepository(ABC):
    @abstractmethod
    def top(self, limit: int = MAX_ENTRIES) -> list[ScoreEntry]: ...

    @abstractmethod
    def add(self, entry: ScoreEntry) -> None: ...

    def best(self) -> int:
        scores = self.top(1)
        return scores[0].score if scores else 0

    def qualifies(self, score: int) -> bool:
        """O placar entra no top 10?"""
        if score <= 0:
            return False
        current = self.top(MAX_ENTRIES)
        return len(current) < MAX_ENTRIES or score > current[-1].score


def _sorted(entries: list[ScoreEntry], limit: int) -> list[ScoreEntry]:
    return sorted(entries, key=lambda e: (-e.score, e.day))[:limit]


class InMemoryHighScoreRepository(HighScoreRepository):
    def __init__(self, entries: list[ScoreEntry] | None = None) -> None:
        self._entries = list(entries or [])

    def top(self, limit: int = MAX_ENTRIES) -> list[ScoreEntry]:
        return _sorted(self._entries, limit)

    def add(self, entry: ScoreEntry) -> None:
        self._entries = _sorted(self._entries + [entry], MAX_ENTRIES)


class SqliteHighScoreRepository(HighScoreRepository):
    def __init__(self, path: Path) -> None:
        import sqlite3  # importado aqui: o navegador não precisa dele

        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path))
        self._db.execute(
            """CREATE TABLE IF NOT EXISTS scores (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   player_name CHAR(3) NOT NULL,
                   score INTEGER NOT NULL CHECK(score >= 0),
                   level INTEGER NOT NULL DEFAULT 1,
                   created_at TEXT NOT NULL
               )"""
        )
        self._db.commit()

    def top(self, limit: int = MAX_ENTRIES) -> list[ScoreEntry]:
        rows = self._db.execute(
            "SELECT player_name, score, level, created_at FROM scores ORDER BY score DESC, id ASC LIMIT ?",
            (limit,),
        ).fetchall()
        return [ScoreEntry(*row) for row in rows]

    def add(self, entry: ScoreEntry) -> None:
        self._db.execute(
            "INSERT INTO scores (player_name, score, level, created_at) VALUES (?, ?, ?, ?)",
            (entry.initials, entry.score, entry.level, entry.day),
        )
        self._db.commit()


class BrowserHighScoreRepository(HighScoreRepository):
    KEY = "coachman.highscores"

    def __init__(self, storage) -> None:  # storage = window.localStorage (pygbag)
        self._storage = storage

    def _load(self) -> list[ScoreEntry]:
        try:
            raw = self._storage.getItem(self.KEY)
            data = json.loads(str(raw)) if raw else []
            return [ScoreEntry(**item) for item in data]
        except Exception:  # dados corrompidos ou storage bloqueado
            return []

    def top(self, limit: int = MAX_ENTRIES) -> list[ScoreEntry]:
        return _sorted(self._load(), limit)

    def add(self, entry: ScoreEntry) -> None:
        entries = _sorted(self._load() + [entry], MAX_ENTRIES)
        try:
            self._storage.setItem(self.KEY, json.dumps([asdict(e) for e in entries]))
        except Exception:
            pass


def create_repository() -> HighScoreRepository:
    """*Factory*: escolhe o repositório certo para a plataforma atual."""
    if sys.platform == "emscripten":
        try:
            import platform as web  # no pygbag, "platform" expõe o objeto window do JS

            return BrowserHighScoreRepository(web.window.localStorage)
        except Exception:
            return InMemoryHighScoreRepository()
    try:
        data_dir = Path(os.environ.get("COACHMAN_DATA", Path.home() / ".coachman"))
        return SqliteHighScoreRepository(data_dir / "scores.db")
    except Exception:
        return InMemoryHighScoreRepository()
