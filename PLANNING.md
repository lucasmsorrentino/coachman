# 🧠 PLANNING.md - Coach-Man

Visão geral do desenvolvimento do **Coach-Man**: o que já foi alcançado e o
que ainda pode vir.

## ✅ Estado atual (v2)

- Jogo reescrito em Python (pygame-ce) com arquitetura em camadas e padrões de
  projeto documentados ([docs/ARQUITETURA.md](docs/ARQUITETURA.md)).
- Versão **web** (WebAssembly via pygbag) publicada pelo GitHub Actions no
  GitHub Pages — sem `.exe` para baixar.
- Jogabilidade e IA fiéis ao arcade ([docs/FANTASMAS.md](docs/FANTASMAS.md)).
- 3 labirintos alternando por fase, tabela de dificuldade do arcade.
- Arte refinada a partir dos originais, por um pipeline reproduzível
  ([docs/ARTE.md](docs/ARTE.md)).
- 61 testes automatizados.

## 🧩 Melhorias planejadas

### 🎮 Jogabilidade
- [x] Direcional contínuo / direção desejada com memória.
- [x] Power-ups temporários com fantasmas vulneráveis.
- [x] Vida extra por pontuação (10.000).
- [x] Pausa no jogo ("P").
- [x] Fim de fase ao coletar todos os "$".
- [ ] Cenas de intervalo ("intermissions") entre fases, como no arcade.

### 🧠 Inteligência Artificial
- [x] Padrões distintos de perseguição (Blinky, Pinky, Inky, Clyde).
- [x] Modo "scatter" (dispersão) alternando com perseguição.
- [x] Estados de vulnerabilidade após power-up.
- [x] Modo Raio-X para visualizar os alvos em tempo real.

### 🧱 Mapa e Visuais
- [x] Novos mapas (Pico dos Marins, Imersão).
- [x] Sistema de fases.
- [x] Telas de transição entre fases.
- [x] Labirinto com bordas arredondadas estilo arcade.
- [x] Múltiplos mapas carregados de dados em texto.
- [ ] Editor de labirintos no navegador.

### 💻 Código e Arquitetura
- [x] Separação de responsabilidades (core / world / actors / systems / scenes / ui).
- [x] Padrão State para os estados do jogo e das cadeiras.
- [x] Testes automatizados.
- [x] Documentação interna do código.

### 🎵 Áudio e Feedback
- [x] Sons de coleta, power-up, cadeirada, morte, vovó e vida extra.
- [x] Liga/desliga do som ("M").
- [ ] Ajuste fino de volume via menu.

### 📦 Distribuição e Interface
- [x] Versão web (substitui o `.exe`).
- [x] Ícone.
- [x] Tela cheia ("F").
- [x] README com prints e GIF.
- [ ] Ranking online (hoje cada navegador guarda o seu).
