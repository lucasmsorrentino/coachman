#!/usr/bin/env python3
"""Gera os diagramas de classes UML (Mermaid) a partir do código-fonte.

    python tools/class_diagram.py          # escreve docs/diagramas/*.mmd e docs/DIAGRAMAS.md

As classes, a herança, os atributos e os métodos públicos são lidos do
próprio código (módulo ``ast``), então o diagrama não "envelhece": rode de
novo depois de mudar o código. Só as associações (quem guarda/usa quem) e os
estereótipos de padrão de projeto são declarados aqui, à mão, e o script
confere se todas as classes citadas existem.

Para gerar as imagens SVG/PNG a partir dos .mmd: ``tools/render_diagrams.js``.
"""
from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "coachman" / "game"
OUT = ROOT / "docs" / "diagramas"
DOC = ROOT / "docs" / "DIAGRAMAS.md"

# --------------------------------------------------------------------------
# Estereótipos: o papel de cada classe nos padrões de projeto
# --------------------------------------------------------------------------
PATTERNS = {
    "App": "Composition Root",
    "GameLoop": "Game Loop",
    "EventBus": "Observer · Subject",
    "CommandTarget": "Command · Receiver",
    "Command": "Command",
    "InputHandler": "Command · Invoker",
    "Scene": "State",
    "SceneStack": "State · pilha",
    "AssetLibrary": "Flyweight",
    "AudioService": "Facade",
    "PygameAudio": "Singleton",
    "NullAudio": "Null Object",
    "HighScoreRepository": "Repository",
    "Actor": "Template Method",
    "Ghost": "Context de State e Strategy",
    "GhostWorld": "interface",
    "GhostState": "State",
    "TargetingStrategy": "Strategy",
    "EntityFactory": "Factory",
    "World": "Mediator",
    "Session": "Observer · assinante",
    "SoundEffects": "Observer · assinante",
    "Popups": "Observer · assinante",
}

# --------------------------------------------------------------------------
# Associações (origem, seta Mermaid, destino, rótulo)
#   *--  composição   o--  agregação   -->  associação
#   ..>  dependência  ..|> realização
# --------------------------------------------------------------------------
RELATIONS = [
    # aplicação / motor
    ("App", "*--", "GameLoop", "loop"),
    ("App", "*--", "SceneStack", "scenes"),
    ("App", "*--", "InputHandler", "input"),
    ("App", "*--", "AssetLibrary", "assets"),
    ("App", "o--", "AudioService", "audio"),
    ("App", "o--", "HighScoreRepository", "scores"),
    ("SceneStack", "o--", "Scene", "pilha"),
    ("Scene", "-->", "App", "app"),
    ("InputHandler", "..>", "Command", "traduz eventos em"),
    ("Command", "..>", "CommandTarget", "execute(alvo)"),
    ("HighScoreRepository", "..>", "ScoreEntry", ""),
    # telas
    ("PlayScene", "*--", "World", "world"),
    ("PlayScene", "*--", "Session", "session"),
    ("PlayScene", "*--", "EventBus", "bus"),
    ("PlayScene", "*--", "SoundEffects", "sfx"),
    ("PlayScene", "*--", "Popups", "popups"),
    ("PlayScene", "-->", "Phase", "phase"),
    ("TitleScene", "..>", "PlayScene", "cria"),
    ("TitleScene", "..>", "HighScoresScene", "empilha"),
    ("TitleScene", "..>", "HelpScene", "empilha"),
    ("TitleScene", "..>", "ExitScene", "empilha"),
    ("PlayScene", "..>", "PauseScene", "empilha"),
    ("PlayScene", "..>", "GameOverScene", "cria"),
    ("GameOverScene", "..>", "InitialsScene", "cria"),
    ("GameOverScene", "..>", "HighScoresScene", "cria"),
    ("InitialsScene", "..>", "HighScoresScene", "cria"),
    ("PauseScene", "..>", "TitleScene", "cria"),
    ("SoundEffects", "-->", "AudioService", "audio"),
    ("SoundEffects", "..>", "EventBus", "assina"),
    ("Popups", "..>", "EventBus", "assina"),
    ("Session", "..>", "EventBus", "assina / publica"),
    # mundo e sistemas
    ("World", "*--", "Maze", "maze"),
    ("World", "*--", "CoachMan", "coachman"),
    ("World", "*--", "Ghost", "ghosts [4]"),
    ("World", "*--", "ModeScheduler", "modes"),
    ("World", "*--", "GhostHouse", "house"),
    ("World", "*--", "Bonus", "bonus"),
    ("World", "-->", "LevelSpec", "spec"),
    ("World", "-->", "EventBus", "publica"),
    ("World", "..>", "EntityFactory", "usa"),
    ("World", "..|>", "GhostWorld", ""),
    ("Maze", "-->", "MazeDefinition", "definition"),
    ("GhostHouse", "-->", "Ghost", "libera"),
    ("GhostHouse", "-->", "LevelSpec", "spec"),
    # atores e IA
    ("Actor", "-->", "Maze", "maze"),
    ("Actor", "-->", "Direction", "direction"),
    ("Ghost", "o--", "GhostState", "state"),
    ("Ghost", "o--", "TargetingStrategy", "strategy"),
    ("Ghost", "-->", "GhostWorld", "world"),
    ("ChaseState", "..>", "TargetingStrategy", "chase_target()"),
    ("TargetingStrategy", "..>", "TargetContext", ""),
    ("EntityFactory", "..>", "CoachMan", "cria"),
    ("EntityFactory", "..>", "Ghost", "cria"),
    ("EntityFactory", "-->", "GhostProfile", "PROFILES"),
]

PACKAGES = {
    "app": "aplicacao",
    "config": "aplicacao",
    "levels": "aplicacao",
    "core": "core",
    "world": "world",
    "actors": "actors",
    "systems": "systems",
    "persistence": "persistence",
    "scenes": "scenes",
}


# --------------------------------------------------------------------------
# Leitura do código
# --------------------------------------------------------------------------
@dataclass
class ClassInfo:
    name: str
    package: str
    module: str
    bases: list[str]
    abstract: bool = False
    kind: str = ""  # enum | dataclass | protocol | event
    fields: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)


def mermaid_type(annotation: ast.expr | None) -> str:
    if annotation is None:
        return ""
    text = ast.unparse(annotation).replace('"', "").replace("'", "")
    text = re.sub(r"\s*\|\s*None", "?", text)
    text = re.sub(r"Callable\[.*\]", "Callable", text)
    text = re.sub(r"\b(?:[a-z_]+\.)+(?=[A-Z])", "", text)  # pygame.mixer.Sound -> Sound, states.X -> X
    return text.replace("[", "~").replace("]", "~")


LITERAL_TYPES = {bool: "bool", int: "int", float: "float", str: "str"}


FUNCTION_RETURNS: dict[str, str] = {}  # funções de módulo -> tipo de retorno (create_audio etc.)


def value_type(value: ast.expr, params: dict[str, ast.expr | None]) -> str:
    """Tipo de ``self.x = <valor>``: anotação do parâmetro, tipo do literal,
    classe instanciada (``EventBus()``) ou retorno de uma fábrica (``create_audio()``)."""
    if isinstance(value, ast.Name) and params.get(value.id) is not None:
        return mermaid_type(params[value.id]).rstrip("?")
    if isinstance(value, ast.Constant) and type(value.value) in LITERAL_TYPES:
        return LITERAL_TYPES[type(value.value)]
    if isinstance(value, ast.BoolOp):  # ex.: audio or create_audio(...)
        for option in value.values:
            found = value_type(option, params)
            if found:
                return found
    if isinstance(value, (ast.List, ast.ListComp)):
        return "list"
    if isinstance(value, (ast.Dict, ast.DictComp)):
        return "dict"
    if isinstance(value, ast.Call):
        func = value.func
        if isinstance(func, ast.Name):
            if func.id[:1].isupper():
                return func.id
            return FUNCTION_RETURNS.get(func.id, "")
        if isinstance(func, ast.Attribute):
            if func.attr[:1].isupper():  # random.Random(), pygame.time.Clock()
                return func.attr
            if isinstance(func.value, ast.Name) and func.value.id[:1].isupper():  # Maze.from_definition()
                return func.value.id
            if func.attr in FUNCTION_RETURNS:
                return FUNCTION_RETURNS[func.attr]
    return ""


def decorator_names(node: ast.FunctionDef) -> set[str]:
    return {ast.unparse(d).split(".")[-1] for d in node.decorator_list}


def collect() -> dict[str, ClassInfo]:
    classes: dict[str, ClassInfo] = {}
    for path in SRC.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):  # funções e métodos
            if isinstance(node, ast.FunctionDef) and node.returns is not None and not node.name.startswith("_"):
                FUNCTION_RETURNS.setdefault(node.name, mermaid_type(node.returns))
    for path in sorted(SRC.rglob("*.py")):
        rel = path.relative_to(SRC)
        if path.name == "__init__.py":
            continue
        package = PACKAGES.get(rel.parts[0].removesuffix(".py"), "aplicacao")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            bases = [ast.unparse(b) for b in node.bases]
            decos = {ast.unparse(d).split("(")[0] for d in node.decorator_list}
            info = ClassInfo(node.name, package, ".".join(rel.with_suffix("").parts), bases)
            if "Enum" in bases:
                info.kind = "enumeration"
            elif "Protocol" in bases:
                info.kind = "interface"
            elif "dataclass" in decos:
                info.kind = "event" if rel.name == "events.py" else "dataclass"
            init_params: dict[str, ast.expr | None] = {}
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    if not item.target.id.startswith("_") and info.kind in ("dataclass", "event"):
                        info.fields.append(f"+{item.target.id}: {mermaid_type(item.annotation)}")
                elif isinstance(item, ast.Assign) and info.kind == "enumeration":
                    info.fields.extend(t.id for t in item.targets if isinstance(t, ast.Name))
                elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    decos_f = decorator_names(item)
                    if "abstractmethod" in decos_f:
                        info.abstract = True
                    if item.name == "__init__":
                        init_params = {a.arg: a.annotation for a in item.args.args[1:]}
                        for stmt in ast.walk(item):
                            pairs: list[tuple[ast.expr, str]] = []
                            if isinstance(stmt, ast.AnnAssign):
                                pairs = [(stmt.target, mermaid_type(stmt.annotation))]
                            elif isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                                target = stmt.targets[0]
                                if isinstance(target, ast.Tuple) and isinstance(stmt.value, ast.Tuple):
                                    pairs = [(t, value_type(v, init_params)) for t, v in zip(target.elts, stmt.value.elts)]
                                else:
                                    pairs = [(target, value_type(stmt.value, init_params))]
                            for target, typ in pairs:
                                if (
                                    isinstance(target, ast.Attribute)
                                    and isinstance(target.value, ast.Name)
                                    and target.value.id == "self"
                                    and not target.attr.startswith("_")
                                    and not any(f.split(":")[0] == f"+{target.attr}" for f in info.fields)
                                ):
                                    info.fields.append(f"+{target.attr}" + (f": {typ}" if typ else ""))
                        continue
                    if item.name.startswith("_"):
                        continue
                    returns = mermaid_type(item.returns)
                    if "property" in decos_f:
                        info.fields.append(f"+{item.name}: {returns}" if returns else f"+{item.name}")
                        continue
                    params = [a.arg for a in item.args.args if a.arg not in ("self", "cls")]
                    marker = "*" if "abstractmethod" in decos_f else "$" if decos_f & {"staticmethod", "classmethod"} else ""
                    info.methods.append(f"+{item.name}({', '.join(params)}){marker}" + (f" {returns}" if returns and returns != "None" else ""))
            if any(b in ("ABC",) for b in bases):
                info.abstract = info.abstract or True
            classes[node.name] = info
    return classes


# --------------------------------------------------------------------------
# Escrita em Mermaid
# --------------------------------------------------------------------------
def stereotype(info: ClassInfo) -> str:
    parts = []
    if info.kind:
        parts.append(info.kind)
    elif info.abstract:
        parts.append("abstract")
    if info.name in PATTERNS:
        parts.append(PATTERNS[info.name])
    return " · ".join(dict.fromkeys(parts))


def class_block(info: ClassInfo, members: bool) -> list[str]:
    lines = [f"    class {info.name} {{"]
    tag = stereotype(info)
    if tag:
        lines.append(f"        <<{tag}>>")
    if members:
        lines += [f"        {f}" for f in info.fields]
        lines += [f"        {m}" for m in info.methods]
    lines.append("    }")
    return lines


def diagram(classes: dict[str, ClassInfo], names: list[str], members: bool, direction: str = "TB") -> str:
    chosen = [n for n in names if n in classes]
    missing = set(names) - set(classes)
    if missing:
        raise SystemExit(f"classes inexistentes no diagrama: {sorted(missing)}")
    chosen_set = set(chosen)
    out = ["classDiagram", f"    direction {direction}"]
    by_package: dict[str, list[ClassInfo]] = {}
    for name in chosen:
        by_package.setdefault(classes[name].package, []).append(classes[name])
    for package, infos in by_package.items():
        out.append(f"    namespace {package} {{")
        for info in infos:
            out += ["    " + line for line in class_block(info, members)]
        out.append("    }")
    for name in chosen:
        for base in classes[name].bases:
            if base in chosen_set:
                out.append(f"    {base} <|-- {name}")
    for src, arrow, dst, label in RELATIONS:
        if src in chosen_set and dst in chosen_set:
            out.append(f"    {src} {arrow} {dst}" + (f" : {label}" if label else ""))
    return "\n".join(out) + "\n"


VIEWS = [
    (
        "1-visao-geral",
        "Visão geral (todas as classes)",
        "Todas as classes do jogo, agrupadas por pacote, com herança e associações. "
        "Os membros estão nos diagramas por área, logo abaixo.",
        None,
        False,
    ),
    (
        "2-ia-das-cadeiras",
        "Atores e IA das cadeiras (Template Method, State, Strategy, Factory)",
        "O núcleo do jogo: o movimento comum (`Actor`), a cadeira como contexto de dois "
        "padrões (`GhostState` e `TargetingStrategy`) e a fábrica que monta tudo.",
        ["Actor", "CoachMan", "Ghost", "GhostWorld", "World", "GhostState", "ScatterState", "ChaseState",
         "FrightenedState", "EatenState", "_HouseMovement", "InHouseState", "LeavingHouseState",
         "EnteringHouseState", "TargetingStrategy", "ShadowTargeting", "AmbushTargeting",
         "WhimsicalTargeting", "PokeyTargeting", "TargetContext", "EntityFactory", "GhostProfile",
         "Direction"],
        True,
    ),
    (
        "3-fase-em-jogo",
        "Uma fase em jogo (Mediator, Observer)",
        "O `World` coordena labirinto, atores e sistemas e publica eventos no `EventBus`; "
        "placar, sons e pop-ups são assinantes.",
        ["PlayScene", "Phase", "World", "Maze", "MazeDefinition", "Bonus", "ModeScheduler", "GhostHouse",
         "LevelSpec", "Session", "SoundEffects", "Popups", "EventBus", "DotEaten", "EnergizerEaten",
         "GhostEaten", "CoachManCaught", "BonusSpawned", "BonusEaten", "ModeChanged", "FrightStarted",
         "FrightEnded", "ExtraLife", "LevelCleared", "AudioService"],
        True,
    ),
    (
        "4-motor-e-infraestrutura",
        "Motor e infraestrutura (Game Loop, Command, Facade, Singleton, Null Object, Repository, Flyweight)",
        "Tudo o que não sabe nada de Pac-Man: laço, entrada, telas, recursos, som e recordes.",
        ["App", "GameLoop", "SceneStack", "Scene", "CommandTarget", "Command", "DirectionCommand",
         "ConfirmCommand", "BackCommand", "PauseCommand", "ToggleDebugCommand", "TextCommand",
         "EraseCommand", "AppCommand", "InputHandler", "AssetLibrary", "AudioService", "PygameAudio",
         "NullAudio", "HighScoreRepository", "InMemoryHighScoreRepository", "SqliteHighScoreRepository",
         "BrowserHighScoreRepository", "ScoreEntry"],
        True,
    ),
    (
        "5-telas",
        "Telas (State com pilha)",
        "Cada tela é um estado da aplicação; as setas tracejadas mostram para onde cada uma leva.",
        ["App", "SceneStack", "CommandTarget", "Scene", "TitleScene", "PlayScene", "PauseScene", "GameOverScene",
         "InitialsScene", "HighScoresScene", "HelpScene", "ExitScene"],
        True,
    ),
]


def main() -> int:
    classes = collect()
    for src, _arrow, dst, _label in RELATIONS:
        for name in (src, dst):
            if name not in classes:
                raise SystemExit(f"associação cita classe inexistente: {name}")
    OUT.mkdir(parents=True, exist_ok=True)
    doc = [
        "# 📐 Diagramas de classes",
        "",
        "Gerados automaticamente a partir do código por "
        "[`tools/class_diagram.py`](../tools/class_diagram.py) (classes, herança, "
        "atributos e métodos públicos lidos do código; associações e papéis nos padrões "
        "declarados no script). O GitHub desenha os blocos Mermaid abaixo; as mesmas "
        "imagens em SVG/PNG ficam em [`img/diagramas/`](img/diagramas/).",
        "",
        "**Legenda (UML):**",
        "",
        "| Desenho | Significado |",
        "|---|---|",
        "| linha cheia com triângulo vazado | herança (é um) |",
        "| linha cheia com losango cheio | composição (o dono cria e guarda) |",
        "| linha cheia com losango vazado | agregação (recebe pronto e guarda) |",
        "| linha cheia com seta | associação (conhece) |",
        "| linha tracejada com seta | dependência (usa ou cria) |",
        "| linha tracejada com triângulo vazado | implementa a interface |",
        "| *itálico* | método abstrato |",
        "| sublinhado | método estático / de classe |",
        "| `«...»` | tipo da classe e o seu papel no padrão de projeto |",
        "",
        "Só os membros públicos aparecem; métodos internos (começados por `_`) foram omitidos.",
        "",
        "Para regenerar:",
        "",
        "```bash",
        "python tools/class_diagram.py                       # .mmd + este arquivo",
        "npm install mermaid@11 playwright && node tools/render_diagrams.js   # SVG/PNG",
        "```",
        "",
    ]
    for slug, title, description, names, members in VIEWS:
        source = diagram(classes, names or list(classes), members, "LR" if names is None else "TB")
        (OUT / f"{slug}.mmd").write_text(source, encoding="utf-8")
        doc += [
            f"## {title}",
            "",
            description,
            "",
            f"![{title}](img/diagramas/{slug}.svg)",
            "",
            "<details><summary>Código Mermaid</summary>",
            "",
            "```mermaid",
            source.rstrip(),
            "```",
            "",
            "</details>",
            "",
        ]
        print(f"{slug}: {len(names or classes)} classes")
    DOC.write_text("\n".join(doc), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
