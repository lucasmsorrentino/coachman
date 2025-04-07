# 🎮 Coach-Man

Coach-Man é um jogo 2D inspirado no clássico Pac-Man, desenvolvido com Python e Pygame. Com uma pegada humorada e temática brasileira, o jogo traz sprites personalizados, trilha sonora temática e IA simples com algoritmo A* para os fantasmas.

## 🕹️ Como jogar

- Use as setas do teclado para mover o **Coach-Man** pelo labirinto.
- Colete todas as "pellets" (bolinhas) para aumentar sua pontuação.
- Evite os fantasmas(cadeiras)! Se colidir com um, você perde uma vida.
- O jogo termina quando todas as vidas acabam.
- Se sua pontuação estiver entre as 10 melhores, você poderá inserir suas iniciais para o ranking de scores.

## 📦 Funcionalidades

- 🎨 Sprites personalizados do Coach-Man e dos fantasmas (Blinky, Pinky, Inky, Clyde).
- 🧠 Movimento dos fantasmas com algoritmo A*.
- 💾 Sistema de placar com SQLite (armazenamento persistente).
- 🔁 Menu interativo com música de fundo.
- 🖼️ Tela de game over estilizada com imagem temática.

## 🚀 Como rodar

1. **Instale as dependências:**

   ```bash
   pip install pygame
   ```

2. **Execute o jogo:**

   ```bash
   python main.py
   ```

   A base de dados `scores.db` será criada automaticamente.

## 📁 Estrutura do Projeto

```
├── main.py              # Ponto de entrada do jogo
├── Game.py              # Gerencia fluxo do jogo e pontuações
├── Engine.py            # Lógica principal do gameplay
├── Menu.py              # Tela inicial e navegação de menu
├── Entity.py            # Entidades: Coachman, Fantasmas, Maze
├── EntityFactory.py     # Criação de personagens com padrão Factory
├── constants.py         # Constantes de cores, grid e layout
├── score_db.py          # Interações com o banco de dados SQLite
├── asset/               # Pasta com sprites e áudios do jogo
└── README.md            # Este arquivo
```

## 🎮 Controles

| Tecla         | Ação                   |
|---------------|------------------------|
| ↑ ↓ ← →       | Movimentar o Coach-Man |
| Enter         | Selecionar opção       |
| Esc / Fechar  | Sair do jogo           |

## 🧠 IA dos Fantasmas

Os fantasmas(cadeiras) utilizam o algoritmo **A\*** para perseguir o jogador, calculando o caminho mais curto no labirinto. Quando o caminho está bloqueado, eles se movimentam aleatoriamente.

## 📝 Créditos e Curiosidades

- O personagem principal é inspirado no influenciador **Pablo Marçal**, com falas e imagens personalizadas no estilo "coach".
- Fontes retrô e trilhas sonoras editadas foram utilizadas para reforçar o estilo arcade.


## 📦 Executável (.exe)

Se você não quiser rodar o jogo pelo código Python, também é possível executá-lo diretamente por um arquivo `.exe` já gerado.

### Como usar o executável:

1. Navegue até a pasta `/dist` do projeto.
2. Verifique se o arquivo `Coach-Man.exe` (ou nome similar) está presente.
3. **Copie a pasta `asset` inteira** (que contém os sprites e áudios) para dentro da mesma pasta onde está o `.exe`.
4. Execute o `.exe` com um duplo clique.

> ⚠️ **Importante**: a pasta `asset` deve estar no mesmo diretório do `.exe`, e com exatamente esse nome, para que o jogo funcione corretamente. Os arquivos de imagem e som são carregados em tempo de execução, e o jogo espera encontrá-los nesse caminho relativo.


## 📌 Requisitos

- Python 3.8+
- Pygame

## 📜 Licença

Este projeto é acadêmico e foi desenvolvido com fins educacionais.

---

Divirta-se com o **Coach-Man** e desbloqueie a prosperidade fugindo dos fantasmas da estagnação! 💪🚀
