"""Constantes globais do jogo.

A geometria segue o arcade original (Namco, 1980): a tela tem 28 x 36 tiles,
sendo 3 linhas de placar em cima, 31 linhas de labirinto e 2 linhas embaixo
(vidas e fase). Cada tile do arcade tem 8 px; aqui usamos 16 px para que os
sprites desenhados à mão (30 x 30 px) tenham a mesma proporção dos originais
(sprite ~= 2 tiles).
"""
from __future__ import annotations

TITLE = "Coach-Man"

TILE = 16
COLS = 28
MAZE_ROWS = 31
HUD_TOP_ROWS = 3
HUD_BOTTOM_ROWS = 2

SCREEN_W = COLS * TILE  # 448
SCREEN_H = (HUD_TOP_ROWS + MAZE_ROWS + HUD_BOTTOM_ROWS) * TILE  # 576
MAZE_Y = HUD_TOP_ROWS * TILE  # deslocamento vertical do labirinto na tela

FPS = 60
DT = 1.0 / FPS  # passo fixo da simulação (ver core/loop.py)

# Velocidade máxima do arcade: 75,757 px/s em tiles de 8 px = 9,47 tiles/s.
# Convertida para pixels por quadro na nossa escala. Todas as velocidades das
# tabelas de fase (levels.py) são percentuais deste valor.
BASE_SPEED = 75.75757625 / 8 * TILE / FPS  # ~2,53 px/quadro

SPRITE = 30  # tamanho dos quadros no atlas

# Pontuação (valores do arcade)
DOT_POINTS = 10
ENERGIZER_POINTS = 50
GHOST_POINTS = (200, 400, 800, 1600)
EXTRA_LIFE_SCORE = 10_000
START_LIVES = 3

# Pausas do arcade (em quadros de 1/60 s)
DOT_PAUSE = 1  # o Pac-Man para 1 quadro ao comer uma bolinha
ENERGIZER_PAUSE = 3  # ... e 3 quadros ao comer um energizador
GHOST_EAT_PAUSE = 60  # congela ~1 s mostrando os pontos
BONUS_DOTS = (70, 170)  # a vovó aparece após comer 70 e 170 bolinhas

# Cores (paleta do arcade)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
PINK = (255, 184, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 184, 82)
DOT_COLOR = (255, 184, 174)
DOOR_COLOR = (255, 184, 255)
HUD_GRAY = (222, 222, 255)

FONT_FILE = "assets/fonts/PressStart2P-Regular.ttf"

# Área tocável do botão de pausa (canto superior direito do placar)
PAUSE_BUTTON = (SCREEN_W - 3 * TILE, 0, 3 * TILE, 3 * TILE)
