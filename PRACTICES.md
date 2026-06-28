# Especificação: Boas Práticas de Desenvolvimento

Este documento define as convenções de código Python e de mensagens de commit Git adotadas neste repositório. O objetivo é manter consistência, legibilidade e rastreabilidade ao longo da evolução do projeto.

---

## Parte I — Boas Práticas de Python

### 1. Estilo de Código

Seguir **PEP 8** (estilo) e **PEP 257** (docstrings) como base. Os pontos abaixo destacam o que é obrigatório:

| Item | Convenção |
|---|---|
| Indentação | 4 espaços, nunca tabs |
| Tamanho máximo de linha | 100 caracteres (mais permissivo que os 79 do PEP 8) |
| Aspas | Aspas duplas `"..."` para strings, simples `'...'` apenas dentro de strings duplas |
| Linhas em branco | 2 entre funções/classes top-level, 1 entre métodos |
| Encoding | UTF-8 sem BOM |
| Final de arquivo | Sempre terminar com uma única linha em branco |

### 2. Convenções de Nomenclatura

| Elemento | Estilo | Exemplo |
|---|---|---|
| Módulo / arquivo | `snake_case` | `genetic_algorithm.py` |
| Função / variável | `snake_case` | `calculate_fitness` |
| Classe | `PascalCase` | `FleetConfig` |
| Constante | `UPPER_SNAKE_CASE` | `MAX_GENERATIONS` |
| "Privado" | Prefixo `_` | `_internal_helper` |
| Genérico / não usado | `_` | `for _ in range(n)` |

Nomes devem ser **descritivos e em inglês** (código), mas **comentários e docstrings podem estar em português** quando facilitar a comunicação no projeto.

### 3. Type Hints

Toda função pública deve ter anotações de tipo nos parâmetros e no retorno:

```python
from typing import List, Tuple, Dict

def calculate_fitness(
    chromosome: List[int],
    cities_by_id: Dict[int, City],
    fleet: FleetConfig,
) -> float:
    ...
```

Para Python 3.9+, prefira `list[int]` a `List[int]`. Use `Optional[X]` (ou `X | None`) explicitamente quando aplicável.

### 4. Docstrings

Padrão **Google Style** ou **NumPy Style** — escolher um e manter consistência no arquivo. Toda função pública, classe e módulo devem ter docstring:

```python
def order_crossover(parent1: list[int], parent2: list[int]) -> list[int]:
    """Realiza o crossover por ordem (OX) entre dois pais.

    Args:
        parent1: Primeiro cromossomo pai (lista de IDs).
        parent2: Segundo cromossomo pai (lista de IDs).

    Returns:
        Cromossomo filho resultante do cruzamento.

    Raises:
        ValueError: Se os pais tiverem comprimentos diferentes.
    """
```

### 5. Imports

Organizar em três blocos, separados por uma linha em branco:

```python
# 1. Biblioteca padrão
import math
import random
from typing import List, Tuple

# 2. Bibliotecas de terceiros
import numpy as np
import pygame

# 3. Módulos locais
from genetic_algorithm import calculate_fitness, mutate
from draw_functions import draw_paths
```

Evitar `from module import *`. Evitar imports relativos (`from .module import x`) em scripts simples.

### 6. Tratamento de Erros

- **Nunca** usar `except:` ou `except Exception:` sem necessidade explícita. Capture exceções específicas.
- **Falhar rápido**: validar entradas no início da função (`assert` em código de debug, `raise ValueError` em código de produção).
- Mensagens de erro devem incluir contexto útil (qual valor causou o problema, não apenas "valor inválido").

```python
# Ruim
if cap < 0:
    raise ValueError("Invalid capacity")

# Bom
if cap < 0:
    raise ValueError(f"Capacity must be non-negative, got {cap}")
```

### 7. Estrutura de Funções

- **Uma função, uma responsabilidade**. Se a docstring começa com "faz X **e** Y", divida em duas.
- **Máximo ~50 linhas por função**. Acima disso, refatorar em helpers.
- **Máximo 5 parâmetros**. Acima disso, agrupar em dataclass.
- **Funções puras quando possível**: evitar efeitos colaterais e estado global.

### 8. Estruturas de Dados

Preferir, em ordem:

1. **`dataclass`** para agrupamentos de dados (com `frozen=True` se imutável).
2. **`NamedTuple`** para tuplas semânticas pequenas.
3. **`dict`** para mapeamentos genéricos.
4. **Classes completas** apenas quando há comportamento real, não só dados.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class City:
    id: int
    x: int
    y: int
    demand: float
    priority: int
```

### 9. Comentários

- Comentar **o porquê**, não o quê. Código bem nomeado dispensa comentários óbvios.
- Comentários `# TODO:` devem incluir contexto: `# TODO(mvgv): substituir por OX modificado quando suportar VRP`.
- Remover código morto. Não deixar blocos comentados — o git já tem o histórico.

### 10. Logging em vez de `print`

Para código que vai além de scripts didáticos, usar `logging`:

```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Geração {gen}: melhor fitness = {best:.2f}")
```

No script principal: `logging.basicConfig(level=logging.INFO)`.

### 11. Testes

- Usar **`pytest`**. Arquivos `test_*.py` em `tests/`.
- Um teste por comportamento, não por função.
- Nome do teste descreve o cenário: `test_order_crossover_preserves_all_clients`.
- Usar **fuzz testing** para invariantes (rodar operador 10000× com entradas aleatórias e validar).
- Cobertura não é meta em si — cubra o que é **arriscado** (operadores genéticos, fitness), não o trivial (getters).

### 12. Ferramentas Recomendadas

| Ferramenta | Propósito | Comando |
|---|---|---|
| **black** | Formatador automático | `black .` |
| **ruff** | Linter + formatter rápido | `ruff check .` |
| **mypy** | Verificação de tipos estática | `mypy genetic_algorithm.py` |
| **pytest** | Framework de testes | `pytest tests/` |
| **pre-commit** | Roda checks antes de commitar | `pre-commit install` |

Configurar em `pyproject.toml` para garantir consistência entre desenvolvedores.

### 13. Dependências

- Listar dependências em `requirements.txt` (ou `pyproject.toml`) com versões pinadas: `pygame==2.5.2`.
- Separar `requirements-dev.txt` para ferramentas de desenvolvimento (pytest, black, ruff).
- Usar **ambientes virtuais** sempre: `python -m venv .venv && .venv/Scripts/activate`.

### 14. Performance

- **Profile antes de otimizar**. Use `cProfile` ou `timeit`, não intuição.
- Evitar `copy.deepcopy` quando `list.copy()` ou slice resolve.
- Evitar reconstruir listas em loop — use list comprehensions ou pre-aloque.
- Para hot paths, considere `numpy` ou estruturas vetorizadas.

---

## Parte II — Commits Semânticos

Adotar o padrão **Conventional Commits** (https://www.conventionalcommits.org/).

### 1. Estrutura do Commit

```
<tipo>(<escopo opcional>): <descrição curta>

<corpo opcional explicando o porquê>

<rodapé opcional com referências/breaking changes>
```

Exemplo completo:

```
feat(genetic): adiciona operador de mutação reallocate

Move uma cidade da rota de um veículo para outro,
permitindo rebalancear carga sem depender apenas do swap.
Resolve gargalo identificado nos testes de fuzz.

Refs: SPEC.md §1.2
```

### 2. Tipos de Commit

| Tipo | Quando usar |
|---|---|
| **feat** | Nova funcionalidade visível ao usuário |
| **fix** | Correção de bug |
| **docs** | Apenas documentação (README, docstrings, SPEC) |
| **style** | Formatação, espaços, ponto-e-vírgula — sem mudança de lógica |
| **refactor** | Reestruturação de código sem mudança de comportamento |
| **perf** | Melhoria de performance |
| **test** | Adicionar ou corrigir testes |
| **build** | Mudanças no sistema de build, dependências (`requirements.txt`) |
| **ci** | Configuração de integração contínua |
| **chore** | Tarefas auxiliares (atualizar `.gitignore`, configs) |
| **revert** | Reverte um commit anterior |

### 3. Escopo (opcional)

Indica a parte do código afetada. Em projetos pequenos, costuma ser o nome do módulo:

- `feat(crossover): ...`
- `fix(fitness): ...`
- `refactor(draw): ...`
- `docs(spec): ...`

### 4. Descrição (linha 1)

- **Imperativo no presente**: "adiciona" (não "adicionado" nem "adicionando").
- **Sem ponto final**.
- **Máximo 72 caracteres** (idealmente 50).
- **Minúscula no início** (exceto nomes próprios).
- **Descreve o quê, não o porquê** (o porquê vai no corpo).

```
✓ feat(genetic): adiciona penalidade de capacidade no fitness
✗ Adicionei a penalidade de capacidade no fitness.
✗ feat: changes
✗ feat(genetic): Add capacity penalty to the fitness function and also small refactor.
```

### 5. Corpo (opcional)

- Separado da descrição por uma linha em branco.
- Quebrar linhas em 72 caracteres.
- Explica **por que** a mudança foi feita, não como (o diff já mostra o como).
- Útil para mudanças não-triviais ou que precisam de contexto histórico.

### 6. Rodapé (opcional)

- **Referências a issues**: `Closes #42`, `Refs #15`.
- **Breaking changes**: linha começando com `BREAKING CHANGE:`, descrevendo o que quebrou e como migrar.
- **Co-autores**: `Co-Authored-By: Nome <email>`.

```
feat(api)!: muda assinatura de calculate_fitness

BREAKING CHANGE: calculate_fitness agora exige FleetConfig
como terceiro parâmetro. Chamadas antigas precisam atualizar.
```

O `!` após o tipo/escopo é um sinal visual adicional de breaking change.

### 7. Exemplos por Tipo

```
feat(scenario): adiciona gerador parametrizável de cenários hospitalares
fix(crossover): corrige passagem de parent1 duplicado em tsp.py
docs(readme): atualiza dependências para incluir numpy e matplotlib
style(draw): formata draw_functions.py com black
refactor(fitness): extrai split_routes em função auxiliar
perf(mutate): substitui deepcopy por list.copy (~8x mais rápido)
test(genetic): adiciona fuzz test de 10000 execuções para order_crossover
build(deps): pino pygame==2.5.2 em requirements.txt
chore(gitignore): ignora __pycache__ e .venv
revert: feat(crossover): reverte mudança da estrutura de duas partes
```

### 8. Anti-padrões a Evitar

```
✗ "fix"                          # sem descrição
✗ "wip"                          # work-in-progress não deveria ser commitado
✗ "update file.py"               # o que mudou? por quê?
✗ "vários arquivos"              # commit gigante e vago
✗ "feat: adds and fixes things"  # mistura tipos
✗ "Asdf"                         # commit de teste esquecido
```

### 9. Granularidade

- **Um commit = uma unidade lógica de mudança**. Pode ter múltiplos arquivos, mas todos contribuindo para a mesma alteração conceitual.
- **Commits pequenos e frequentes** são preferíveis a commits gigantes raros.
- **Não misture tipos**: refactor + feat = dois commits.
- Use `git add -p` para revisar mudanças e dividir em commits coesos.

### 10. Histórico Limpo

- Evitar `git commit --amend` em commits já enviados (force-push reescreve histórico de outros).
- Em branches de feature local, `rebase -i` é aceitável para limpar antes de abrir PR.
- **Nunca** force-push em `main` ou branches compartilhadas.

### 11. Branches

Convenção de nomes:

| Prefixo | Propósito |
|---|---|
| `feat/` | Nova funcionalidade |
| `fix/` | Correção de bug |
| `refactor/` | Refatoração |
| `docs/` | Mudanças apenas em documentação |
| `chore/` | Tarefas diversas |

Exemplos: `feat/vrp-crossover`, `fix/roulette-zero-fitness`, `docs/practices-spec`.

### 12. Pull Requests

- Título do PR segue o mesmo padrão de commit: `feat(genetic): suporta VRP com restrições`.
- Descrição do PR explica **o porquê** e como testar (Test Plan).
- PR pequeno > PR grande. Se passar de ~400 linhas mudadas, considere dividir.

---

## Parte III — Verificação e Adoção

### Checklist antes de commitar

- [ ] Código formatado (`black .` ou equivalente)
- [ ] Linter sem warnings (`ruff check .`)
- [ ] Type hints presentes em funções públicas
- [ ] Testes passando (`pytest`)
- [ ] Docstring atualizada se assinatura mudou
- [ ] Mensagem de commit segue Conventional Commits
- [ ] Sem código morto, sem `print` esquecido, sem `TODO` sem contexto

### Onboarding

Novos contribuidores devem:

1. Ler este `PRACTICES.md` e o `SPEC.md`.
2. Instalar dependências de dev (`pip install -r requirements-dev.txt`).
3. Configurar `pre-commit install` para garantir checks automáticos.
4. Fazer um commit de teste em branch própria para validar o setup.

### Evolução desta especificação

Mudanças neste documento devem ser feitas via PR com tipo `docs(practices)`. Decisões coletivas devem ser registradas no corpo do commit para preservar o "porquê".
