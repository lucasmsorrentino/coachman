# 🧠 PLANNING.md - Coach-Man

Este documento descreve a visão geral de desenvolvimento do jogo **Coach-Man**, incluindo os objetivos alcançados até agora e as metas futuras de aprimoramento.

## ✅ Estado Atual

- Base funcional do jogo desenvolvida com Pygame.
- Personagem principal (Coach-Man) com sprites e animação.
- Fantasmas com IA baseada no algoritmo A*.
- Sistema de placar persistente com SQLite.
- Menu inicial funcional com música.
- Tela de game over personalizada.
- Executável (.exe) disponível para usuários finais.
- Mapa e layout inicial com movimentação funcional.

## 🧩 Melhorias Futuras Planejadas

### 🎮 Jogabilidade
- [ ] Direcional contínuo: manter movimento enquanto a tecla estiver pressionada.
- [ ] Adição de power-ups temporários (ex: invencibilidade, fantasma vulnerável).
- [ ] Sistema de vidas extras baseado em pontuação.
- [ ] Pausa no jogo (pressionando "P").
- [ ] Fim de fase ao coletar todos os pellets.

### 🧠 Inteligência Artificial
- [ ] Melhorar a IA dos fantasmas com padrões distintos de perseguição (inspirados no Pac-Man original).
- [ ] Adicionar comportamento de “scatter” (fantasmas se afastam por alguns segundos).
- [ ] Estados de vulnerabilidade após power-up.

### 🧱 Mapa e Visuais
- [ ] Criar novos mapas com maior complexidade.
- [ ] Sistema de fases (ex: fase 1, fase 2, etc).
- [ ] Telas de transição entre fases.
- [ ] Melhorar design visual do labirinto (ex: tiles com bordas).
- [ ] Suporte a múltiplos mapas carregados dinamicamente.

### 💻 Código e Arquitetura
- [ ] Refatorar o código para melhor separação de responsabilidades.
- [ ] Implementar padrão State para os estados do jogo.
- [ ] Criar testes automatizados básicos.
- [ ] Documentação interna do código.

### 🎵 Áudio e Feedback
- [ ] Sons para coleta de pellet(no score), perda de vida e game over.

- [ ] Ajuste de volumes via menu.

### 📦 Distribuição e Interface
- [ ] Adicionar ícone ao .exe.
- [ ] Tela de configurações (ex: volume, resolução).
- [ ] Adicionar opção fullscreen.
- [ ] Melhorar README e adicionar prints ou GIFs.

---

