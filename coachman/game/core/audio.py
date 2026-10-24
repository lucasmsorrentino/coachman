"""Som -- padrões **Facade**, **Singleton** e **Null Object**.

* **Facade** (GoF, p. 185): o resto do jogo só conhece ``play_music("menu")``
  e ``play_sfx("dot")``; detalhes do ``pygame.mixer`` (canais, volume,
  formatos, mudo) ficam escondidos aqui.
* **Singleton** (GoF, p. 127): o mixer de áudio é um recurso único do sistema;
  ``PygameAudio`` garante uma única instância. Mesmo assim ela é *injetada*
  nas cenas (não buscada globalmente), o que mantém o código testável.
* **Null Object** (Bobby Woolf, *PLoP 3*, 1998): ``NullAudio`` tem a mesma
  interface e não faz nada. É usado nos testes e quando o dispositivo de som
  não está disponível -- ninguém precisa escrever ``if audio is not None``.

As faixas originais têm voz humana: são tocadas na qualidade original
(OGG Vorbis 44,1 kHz estéreo), sem nenhuma conversão para 8 bits.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import pygame

MUSIC = {
    "menu": "assets/audio/menu.ogg",
    "gameplay": "assets/audio/gameplay.ogg",
    "highscores": "assets/audio/highscores.ogg",
}
SFX = ("dot", "dot2", "power", "eat_ghost", "death", "bonus", "extra_life", "menu_move", "menu_select")


class AudioService(ABC):
    muted: bool = False

    @abstractmethod
    def play_music(self, name: str, loops: int = -1) -> None: ...

    @abstractmethod
    def stop_music(self) -> None: ...

    def pause_music(self) -> None: ...

    def resume_music(self) -> None: ...

    @abstractmethod
    def play_sfx(self, name: str) -> None: ...

    @abstractmethod
    def set_muted(self, muted: bool) -> None: ...

    def toggle_mute(self) -> bool:
        self.set_muted(not self.muted)
        return self.muted


class NullAudio(AudioService):
    def __init__(self) -> None:
        self.played: list[str] = []  # útil para testes

    def play_music(self, name: str, loops: int = -1) -> None:
        self.played.append(f"music:{name}")

    def stop_music(self) -> None: ...

    def play_sfx(self, name: str) -> None:
        self.played.append(f"sfx:{name}")

    def set_muted(self, muted: bool) -> None:
        self.muted = muted


class PygameAudio(AudioService):
    _instance: "PygameAudio | None" = None

    MUSIC_VOLUME = 0.7
    SFX_VOLUME = 0.45

    def __new__(cls, base_dir: Path) -> "PygameAudio":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._ready = False
        return cls._instance

    def __init__(self, base_dir: Path) -> None:
        if self._ready:
            return
        self.base_dir = base_dir
        self.current: str | None = None
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        for name in SFX:
            try:
                sound = pygame.mixer.Sound(str(base_dir / f"assets/audio/sfx_{name}.ogg"))
                sound.set_volume(self.SFX_VOLUME)
                self.sounds[name] = sound
            except (pygame.error, FileNotFoundError):  # pragma: no cover - depende do sistema
                pass
        pygame.mixer.set_num_channels(16)
        self._ready = True

    def play_music(self, name: str, loops: int = -1) -> None:
        if name == self.current and pygame.mixer.music.get_busy():
            return
        try:
            pygame.mixer.music.load(str(self.base_dir / MUSIC[name]))
            pygame.mixer.music.set_volume(0 if self.muted else self.MUSIC_VOLUME)
            pygame.mixer.music.play(loops)
            self.current = name
        except pygame.error:  # pragma: no cover
            self.current = None

    def stop_music(self) -> None:
        pygame.mixer.music.stop()
        self.current = None

    def pause_music(self) -> None:
        pygame.mixer.music.pause()

    def resume_music(self) -> None:
        pygame.mixer.music.unpause()

    def play_sfx(self, name: str) -> None:
        if not self.muted and name in self.sounds:
            self.sounds[name].play()

    def set_muted(self, muted: bool) -> None:
        self.muted = muted
        pygame.mixer.music.set_volume(0 if muted else self.MUSIC_VOLUME)


def create_audio(base_dir: Path) -> AudioService:
    """*Factory*: devolve o áudio real ou o Null Object se não houver som."""
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(44100, -16, 2, 1024)
        return PygameAudio(base_dir)
    except pygame.error:
        return NullAudio()
