#!/usr/bin/env python3
"""Pipeline de assets do Coach-Man.

Lê a arte ORIGINAL desenhada à mão (``assets-src/original``) e gera os
arquivos usados pelo jogo em ``coachman/assets``. Nada é editado à mão na
pasta de saída: para mudar um sprite, edite o original e rode de novo::

    python tools/build_assets.py

Requisitos: Pillow e ffmpeg (este último apenas para converter o áudio).

O que o pipeline faz (detalhes em ``docs/ARTE.md``):

* Coach-Man: remove o "halo" semitransparente que sobrou do redimensionamento
  (pixels de borda viram contorno sólido), apaga pixels soltos e mantém as
  cores originais -> sprite nítido, estética 8-bit.
* Cadeiras (fantasmas): o Blinky foi desenhado com sombreamento; Pinky, Inky
  e Clyde eram só silhuetas chapadas. Aqui o sombreamento do Blinky é
  reduzido a 5 tons e reaplicado nas cores escolhidas para cada fantasma.
* Gera os quadros que faltavam: cadeira assustada (azul), piscando (branca),
  "espírito" da cadeira (devorada, voltando para casa) e a animação de morte
  do Coach-Man.
* Bolinhas: um "$" em pixel art. Power-ups: os ícones das redes sociais das
  big techs (``powerup1..4.png``), mantidos exatamente como desenhados, mais
  Facebook, Discord e WhatsApp desenhados aqui no mesmo estilo (20 x 20 px).
* Vovó (a "frutinha" de bônus) e ícone do site: remove o fundo opaco.
* Áudio: as faixas têm voz humana, então NÃO há redução de bits. São apenas
  compactadas para OGG Vorbis estéreo 44,1 kHz em qualidade alta (q7),
  formato recomendado pelo pygbag para o navegador.
* Efeitos sonoros: sintetizados aqui mesmo (16 bits, 44,1 kHz), sem
  material de terceiros.

Todos os sprites são empacotados num único *atlas* (``sprites.png`` +
``sprites.json``), carregado uma única vez e compartilhado por todas as
entidades (padrão Flyweight, ver ``docs/ARQUITETURA.md``).
"""
from __future__ import annotations

import json
import math
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets-src" / "original"
OUT = ROOT / "coachman" / "assets"

CELL = 30  # tamanho de cada quadro no atlas (o mesmo dos desenhos originais)
OUTLINE = (18, 20, 46)  # azul-marinho do contorno do Coach-Man

# Cores-base escolhidas para cada cadeira (as mesmas da versão original).
GHOST_COLORS = {
    "blinky": (200, 14, 10),
    "pinky": (255, 105, 180),
    "inky": (0, 255, 255),
    "clyde": (255, 165, 0),
}
FRIGHT_BLUE = (33, 33, 222)  # azul do "modo assustado" do arcade
FLASH_WHITE = (236, 236, 255)

Pixel = tuple[int, int, int, int]


# --------------------------------------------------------------------------
# utilidades de imagem
# --------------------------------------------------------------------------
def load(name: str) -> Image.Image:
    return Image.open(SRC / name).convert("RGBA")


def components(img: Image.Image) -> list[list[tuple[int, int]]]:
    """Componentes conexos (vizinhança-8) dos pixels opacos."""
    w, h = img.size
    px = img.load()
    seen: set[tuple[int, int]] = set()
    comps = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] == 0 or (x, y) in seen:
                continue
            stack, comp = [(x, y)], []
            seen.add((x, y))
            while stack:
                cx, cy = stack.pop()
                comp.append((cx, cy))
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen and px[nx, ny][3]:
                            seen.add((nx, ny))
                            stack.append((nx, ny))
            comps.append(comp)
    return sorted(comps, key=len, reverse=True)


def remove_specks(img: Image.Image, max_size: int = 20) -> Image.Image:
    """Apaga ilhas de pixels pequenas, separadas do desenho principal."""
    px = img.load()
    for comp in components(img)[1:]:
        if len(comp) <= max_size:
            for x, y in comp:
                px[x, y] = (0, 0, 0, 0)
    return img


def crisp_alpha(img: Image.Image, threshold: int = 110, edge=OUTLINE) -> Image.Image:
    """Transforma o anti-aliasing em pixels sólidos (visual 8-bit).

    Pixels quase transparentes somem; pixels de borda semitransparentes viram
    opacos, misturados com a cor do contorno, preservando a silhueta.
    """
    img = img.copy()
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < threshold:
                px[x, y] = (0, 0, 0, 0)
            elif a < 255:
                t = a / 255
                px[x, y] = (
                    round(r * t + edge[0] * (1 - t)),
                    round(g * t + edge[1] * (1 - t)),
                    round(b * t + edge[2] * (1 - t)),
                    255,
                )
    return img


def remove_background(img: Image.Image, tolerance: int = 40) -> Image.Image:
    """Remove um fundo opaco por *flood fill* a partir das bordas."""
    img = img.copy()
    px = img.load()
    w, h = img.size
    ref = px[0, 0]

    def close(p: Pixel) -> bool:
        return p[3] > 0 and sum(abs(p[i] - ref[i]) for i in range(3)) <= tolerance

    stack = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    seen = set()
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h):
            continue
        seen.add((x, y))
        if not close(px[x, y]):
            continue
        px[x, y] = (0, 0, 0, 0)
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return img


def outline_only(img: Image.Image, color=(200, 230, 255), alpha=230) -> Image.Image:
    """Mantém só o contorno da silhueta (o "espírito" da cadeira)."""
    w, h = img.size
    src = img.load()
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dst = out.load()
    for y in range(h):
        for x in range(w):
            if not src[x, y][3]:
                continue
            border = any(
                not (0 <= x + dx < w and 0 <= y + dy < h) or not src[x + dx, y + dy][3]
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
            )
            if border:
                dst[x, y] = color + (alpha,)
    return out


# --------------------------------------------------------------------------
# cadeiras: sombreamento em 5 tons reaplicado em cada cor
# --------------------------------------------------------------------------
def tone_levels(frames: list[Image.Image], k: int = 5) -> list[float]:
    """K-means 1D sobre o brilho (V) dos pixels do Blinky."""
    values = sorted(max(p[:3]) for f in frames for p in f.getdata() if p[3])
    centers = [values[int((i + 0.5) * len(values) / k)] for i in range(k)]
    for _ in range(30):
        groups: list[list[int]] = [[] for _ in centers]
        for v in values:
            groups[min(range(k), key=lambda i: abs(v - centers[i]))].append(v)
        centers = [sum(g) / len(g) if g else c for g, c in zip(groups, centers)]
    return sorted(centers)


def ramp(base: tuple[int, int, int], levels: list[float]) -> list[tuple[int, int, int]]:
    """Gera os 5 tons de uma cor-base a partir dos níveis do Blinky.

    O tom mais frequente (índice 3) é a própria cor escolhida; tons abaixo
    escurecem proporcionalmente e o tom de brilho clareia em direção ao branco.
    """
    main = levels[3]
    tones = []
    for lv in levels:
        f = lv / main
        if f <= 1:
            tones.append(tuple(round(c * f) for c in base))
        else:
            tones.append(tuple(round(c + (255 - c) * min(1.0, (f - 1) * 3.5)) for c in base))
    return tones


def recolor(frame: Image.Image, levels: list[float], tones: list[tuple[int, int, int]]) -> Image.Image:
    out = frame.copy()
    px = out.load()
    w, h = out.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if not a:
                continue
            v = max(r, g, b)
            i = min(range(len(levels)), key=lambda j: abs(v - levels[j]))
            px[x, y] = tones[i] + (255,)
    return out


# --------------------------------------------------------------------------
# animação de morte do Coach-Man (a boca abre até ele sumir, como no arcade)
# --------------------------------------------------------------------------
def death_frames(base: Image.Image, steps: int = 11) -> list[Image.Image]:
    frames = []
    cx, cy = CELL / 2, CELL / 2
    for i in range(steps):
        half = 20 + (180 - 20) * (i / (steps - 1)) ** 1.2  # meia-abertura em graus
        mask = Image.new("L", (CELL, CELL), 255)
        if half >= 179.5:
            mask = Image.new("L", (CELL, CELL), 0)
        else:
            d = ImageDraw.Draw(mask)
            # 0 graus = direita no PIL; "para cima" = 270
            d.pieslice([cx - 30, cy - 30, cx + 30, cy + 30], 270 - half, 270 + half, fill=0)
        frame = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
        frame.paste(base, (0, 0), Image.composite(base.getchannel("A"), Image.new("L", base.size, 0), mask))
        frames.append(frame)
    # "estouro" final: pequenos raios amarelos
    for radius in (6, 10):
        frame = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
        d = ImageDraw.Draw(frame)
        for k in range(8):
            ang = k * math.pi / 4
            x0, y0 = cx + math.cos(ang) * (radius - 4), cy + math.sin(ang) * (radius - 4)
            x1, y1 = cx + math.cos(ang) * radius, cy + math.sin(ang) * radius
            d.line([x0, y0, x1, y1], fill=(255, 220, 40, 255), width=2)
        frames.append(frame)
    return frames


# --------------------------------------------------------------------------
# "$": a bolinha comum do labirinto
# --------------------------------------------------------------------------
DOLLAR = (
    "..#..",
    ".####",
    "#.#..",
    ".###.",
    "..#.#",
    "####.",
    "..#..",
)
DOLLAR_COLOR = (110, 235, 120)


def glyph(rows: tuple[str, ...], color: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGBA", (len(rows[0]), len(rows)), (0, 0, 0, 0))
    for y, line in enumerate(rows):
        for x, ch in enumerate(line):
            if ch == "#":
                img.putpixel((x, y), color + (255,))
    return img


# --------------------------------------------------------------------------
# Facebook, Discord e WhatsApp: mesmos 20x20 px com cantos arredondados dos originais
# --------------------------------------------------------------------------
FACEBOOK_BG = (24, 119, 242)
FACEBOOK_F = (
    "...####",
    "..#####",
    "..###..",
    "..###..",
    "#######",
    "#######",
    "..###..",
    "..###..",
    "..###..",
    "..###..",
    "..###..",
    "..###..",
    "..###..",
    "..###..",
)
DISCORD_BG = (88, 101, 242)
DISCORD_FACE = (
    "...##....##...",
    ".############.",
    "##############",
    "##############",
    "###..####..###",
    "##....##....##",
    "##....##....##",
    "###..####..###",
    "##############",
    ".###......###.",
    "..##......##..",
)

WHATSAPP_BG = (37, 211, 102)
WHATSAPP_PHONE = (
    "....######....",
    "..##......##..",
    ".#..........#.",
    ".#.##.......#.",
    "#..###.......#",
    "#..##........#",
    "#...##.......#",
    "#....##..##..#",
    "#.....#####..#",
    "#.......##...#",
    ".#..........#.",
    "##.........#..",
    "#.##.....##...",
    "....#####.....",
)


def social_icon(bg: tuple[int, int, int], symbol: tuple[str, ...], offset: tuple[int, int]) -> Image.Image:
    icon = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    ImageDraw.Draw(icon).rounded_rectangle([5, 5, 24, 24], radius=4, fill=bg + (255,))
    # sombra discreta embaixo, como nos ícones desenhados à mão
    ImageDraw.Draw(icon).line([7, 24, 22, 24], fill=tuple(c * 3 // 4 for c in bg) + (255,))
    icon.alpha_composite(glyph(symbol, (255, 255, 255)), (5 + offset[0], 5 + offset[1]))
    return icon


# --------------------------------------------------------------------------
# atlas
# --------------------------------------------------------------------------
def build_sprites() -> None:
    frames: dict[str, Image.Image] = {}

    # Coach-Man: 0 = boca aberta, 1 = meio aberta, 2 = fechada
    for d in ("Right", "Left", "Up", "Down"):
        for i in range(3):
            img = crisp_alpha(load(f"coachMan{d}0{i + 1}.png"))
            frames[f"coachman.{d.lower()}.{i}"] = remove_specks(img)
    for i, f in enumerate(death_frames(frames["coachman.up.0"])):
        frames[f"coachman.death.{i}"] = f

    # Cadeiras
    blinky = [load(f"BLINKY{i:02d}.png") for i in range(1, 9)]
    levels = tone_levels(blinky)
    palettes = {name: ramp(color, levels) for name, color in GHOST_COLORS.items()}
    palettes["frightened"] = ramp(FRIGHT_BLUE, levels)
    palettes["flash"] = [(150, 150, 190), (185, 185, 220), (210, 210, 240), FLASH_WHITE, (255, 255, 255)]
    for name, tones in palettes.items():
        for i, f in enumerate(blinky):
            frames[f"ghost.{name}.{i}"] = recolor(f, levels, tones)
    for i, f in enumerate(blinky):
        frames[f"ghost.eaten.{i}"] = outline_only(f)

    # Power-ups (ícones das redes sociais): os 4 originais mantidos exatamente
    # como desenhados + Facebook, Discord e WhatsApp em pixel art no mesmo estilo.
    for i in range(4):
        frames[f"powerup.{i}"] = load(f"powerup{i + 1}.png")
    frames["powerup.4"] = social_icon(FACEBOOK_BG, FACEBOOK_F, (6, 6))
    frames["powerup.5"] = social_icon(DISCORD_BG, DISCORD_FACE, (3, 5))
    frames["powerup.6"] = social_icon(WHATSAPP_BG, WHATSAPP_PHONE, (3, 3))

    # Bolinha padrão: um "$" em pixel art (prosperidade desbloqueada!)
    frames["dot.dollar"] = glyph(DOLLAR, DOLLAR_COLOR)

    # Vovó (bônus): remove o fundo preto e reduz para o tamanho de um quadro
    vovo = remove_background(load("vovo.png"), tolerance=60)
    vovo = vovo.resize((CELL, CELL), Image.Resampling.LANCZOS)
    frames["bonus.vovo"] = remove_specks(crisp_alpha(vovo, threshold=128, edge=(40, 60, 70)), 6)

    names = list(frames)
    cols = 8
    rows = math.ceil(len(names) / cols)
    atlas = Image.new("RGBA", (cols * CELL, rows * CELL), (0, 0, 0, 0))
    index = {}
    for n, name in enumerate(names):
        x, y = (n % cols) * CELL, (n // cols) * CELL
        atlas.alpha_composite(frames[name], (x, y))
        index[name] = [x, y, *frames[name].size]
    (OUT / "sprites").mkdir(parents=True, exist_ok=True)
    atlas.save(OUT / "sprites" / "sprites.png", optimize=True)
    (OUT / "sprites" / "sprites.json").write_text(json.dumps(index, indent=1), encoding="utf-8")
    print(f"atlas: {len(names)} quadros -> {atlas.size}")


def build_images() -> None:
    out = OUT / "images"
    out.mkdir(parents=True, exist_ok=True)

    # Tela de título: retrato inteiro (448x448) na parte de baixo de uma tela
    # 448x576; a faixa de cima é preenchida com o mesmo azul do fundo.
    head = load("marcalHead.png")
    title = Image.new("RGBA", (448, 576), head.getpixel((4, 4)))
    title.alpha_composite(head.resize((448, 448), Image.Resampling.LANCZOS), (0, 128))
    title.convert("RGB").save(out / "title.png", optimize=True)

    load("marcalHead7.png").resize((448, 251), Image.Resampling.LANCZOS).convert("RGB").save(out / "exit.png", optimize=True)

    amb = Image.open(SRC / "pablo-marcal-ambulancia.jpg").convert("RGB")
    amb.resize((448, round(448 * amb.height / amb.width)), Image.Resampling.LANCZOS).save(out / "gameover.jpg", quality=88)

    # Ícone: o Coach-Man comendo, sem o fundo cinza, ampliado sem suavização.
    icon = remove_specks(remove_background(load("CoachmanEatingRight.png"), tolerance=110), 6)
    canvas = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    canvas.alpha_composite(icon, (1, 1))
    canvas.resize((64, 64), Image.Resampling.NEAREST).save(out / "icon.png")
    canvas.resize((64, 64), Image.Resampling.NEAREST).save(OUT.parent / "favicon.png")


def build_fonts() -> None:
    out = OUT / "fonts"
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC / "PressStart2P-Regular.ttf", out / "PressStart2P-Regular.ttf")
    shutil.copyfile(SRC / "OFL-PressStart2P.txt", out / "OFL.txt")


# --------------------------------------------------------------------------
# áudio
# --------------------------------------------------------------------------
MUSIC = {
    # arquivo original -> nome usado pelo jogo
    "videoplayback_audio.wav": "menu.ogg",
    "audio_extraido.wav": "gameplay.ogg",
    "audio_cortado.wav": "highscores.ogg",
}
RATE = 44100


def to_ogg(src: Path, dst: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ar", str(RATE), "-c:a", "libvorbis", "-q:a", "7", str(dst)],
        check=True,
    )


def write_wav(path: Path, samples: list[float]) -> None:
    peak = max(1e-9, max(abs(s) for s in samples))
    gain = 0.8 / peak
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)  # 16 bits
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, s * gain)) * 32767)) for s in samples))


def env(t: float, dur: float, attack: float = 0.005) -> float:
    if t < attack:
        return t / attack
    return max(0.0, 1 - (t - attack) / max(1e-6, dur - attack)) ** 2


def tone(freq_fn, dur: float, harmonics=(1.0,), attack=0.005) -> list[float]:
    n = int(dur * RATE)
    out, phase = [], 0.0
    for i in range(n):
        t = i / RATE
        phase += 2 * math.pi * freq_fn(t) / RATE
        s = sum(a * math.sin(phase * (h + 1)) for h, a in enumerate(harmonics))
        out.append(s * env(t, dur, attack))
    return out


def mix(*tracks: tuple[float, list[float]]) -> list[float]:
    n = max(int(off * RATE) + len(tr) for off, tr in tracks)
    out = [0.0] * n
    for off, tr in tracks:
        o = int(off * RATE)
        for i, s in enumerate(tr):
            out[o + i] += s
    return out


def sfx_bank() -> dict[str, list[float]]:
    """Efeitos suaves (senoidais, 16 bits) - nada de chiptune."""
    rnd = random.Random(7)

    def knock(dur=0.22):  # "cadeirada": batida de madeira (ruído filtrado + grave)
        n = int(dur * RATE)
        out, lp = [], 0.0
        for i in range(n):
            t = i / RATE
            lp += 0.25 * (rnd.uniform(-1, 1) - lp)
            body = math.sin(2 * math.pi * (140 - 60 * t / dur) * t)
            out.append((0.9 * lp + 0.8 * body) * env(t, dur, 0.002))
        return out

    return {
        "dot": tone(lambda t: 660 + 500 * t / 0.05, 0.05, (1.0, 0.2)),
        "dot2": tone(lambda t: 520 + 380 * t / 0.05, 0.05, (1.0, 0.2)),
        "power": mix(*[(k * 0.07, tone(lambda t, f=f: f, 0.25, (1.0, 0.3, 0.1))) for k, f in enumerate((392, 523, 659, 784))]),
        "eat_ghost": mix((0, knock()), (0.05, tone(lambda t: 500 + 1400 * t / 0.3, 0.3, (1.0, 0.25)))),
        "death": tone(lambda t: 760 * (1 - t / 1.6) ** 1.6 + 70 + 18 * math.sin(2 * math.pi * 9 * t), 1.6, (1.0, 0.35, 0.1), 0.01),
        "bonus": mix((0, tone(lambda t: 988, 0.18, (1.0, 0.5))), (0.09, tone(lambda t: 1319, 0.3, (1.0, 0.5)))),
        "extra_life": mix(*[(k * 0.1, tone(lambda t, f=f: f, 0.35, (1.0, 0.4, 0.15))) for k, f in enumerate((523, 659, 784, 1047))]),
        "menu_move": tone(lambda t: 880, 0.06, (1.0, 0.3)),
        "menu_select": mix((0, tone(lambda t: 660, 0.1, (1.0, 0.3))), (0.07, tone(lambda t: 990, 0.18, (1.0, 0.3)))),
    }


def build_audio() -> None:
    out = OUT / "audio"
    out.mkdir(parents=True, exist_ok=True)
    for src, dst in MUSIC.items():
        to_ogg(SRC / src, out / dst)
    with tempfile.TemporaryDirectory() as tmp:
        for name, samples in sfx_bank().items():
            wav = Path(tmp) / f"{name}.wav"
            write_wav(wav, samples)
            to_ogg(wav, out / f"sfx_{name}.ogg")
    print("audio:", ", ".join(sorted(p.name for p in out.iterdir())))


def build_comparison() -> None:
    """Imagem "antes x depois" usada em docs/ARTE.md."""
    zoom, pad = 4, 6
    atlas = Image.open(OUT / "sprites" / "sprites.png")
    index = json.loads((OUT / "sprites" / "sprites.json").read_text(encoding="utf-8"))

    def new(name: str) -> Image.Image:
        x, y, w, h = index[name]
        return atlas.crop((x, y, x + w, y + h))

    rows = [
        [load(f"coachMan{d}0{i}.png") for d in ("Right", "Up") for i in (1, 2, 3)],
        [new(f"coachman.{d}.{i}") for d in ("right", "up") for i in range(3)],
        [load(f"{n}01.png") for n in ("BLINKY", "PINKY", "INKY", "CLYDE")] + [load("vovo.png").resize((CELL, CELL))],
        [new(f"ghost.{n}.0") for n in ("blinky", "pinky", "inky", "clyde")] + [new("bonus.vovo")],
        [new(f"ghost.{n}.{i}") for n, i in (("frightened", 1), ("flash", 2), ("eaten", 3))]
        + [new(f"coachman.death.{i}") for i in (3, 7, 11)],
    ]
    cols = max(len(r) for r in rows)
    cell = CELL * zoom + pad
    sheet = Image.new("RGBA", (cols * cell + pad, len(rows) * cell + pad), (16, 16, 32, 255))
    for r, row in enumerate(rows):
        for c, img in enumerate(row):
            sheet.alpha_composite(img.resize((CELL * zoom, CELL * zoom), Image.Resampling.NEAREST), (pad + c * cell, pad + r * cell))
    target = ROOT / "docs" / "img" / "arte_antes_depois.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target, optimize=True)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    build_sprites()
    build_images()
    build_fonts()
    build_comparison()
    if "--no-audio" not in sys.argv:
        build_audio()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
