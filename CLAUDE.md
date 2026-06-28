# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Documentação, docstrings e comentários neste repositório são em **português**; o código (nomes de identificadores) é em inglês. Mantenha essa convenção. As regras detalhadas de estilo e de commit estão em `PRACTICES.md`; a especificação funcional do VRP está em `SPEC.md`.

## Executando

Use o ambiente virtual já existente em `.venv` (Python 3.12).

```bash
.venv/Scripts/python.exe tsp.py        # visualizador principal (Pygame); loop infinito do AG, sai com Q ou fechando a janela
.venv/Scripts/python.exe demo_crossover.py   # demo isolada e LEGADA de OX (TSP, não importa o pacote)
.venv/Scripts/python.exe demo_mutation.py    # demo isolada e LEGADA de mutação (TSP, não importa o pacote)
```

Instalação de dependências: `pip install -r requirements.txt` (runtime) e `pip install -r requirements-dev.txt` (pytest/black/ruff/mypy). Versões são pinadas.

## Testes e qualidade

```bash
.venv/Scripts/python.exe -m pytest -q            # roda toda a suíte (tests/)
.venv/Scripts/python.exe -m pytest tests/test_genetic_algorithm.py::test_calculate_fitness   # um único teste
.venv/Scripts/python.exe -m ruff check .         # linter
.venv/Scripts/python.exe -m black .              # formatador
.venv/Scripts/python.exe -m mypy genetic_algorithm.py   # checagem de tipos
```

Não há `pyproject.toml`/`setup.cfg`: ruff, black e mypy rodam com defaults (note que `PRACTICES.md` pede linha de 100 chars, mas nenhum config impõe isso — o default de black/ruff é 88). Os testes cobrem o que é arriscado (operadores genéticos, `split_routes`, fitness) e incluem **fuzz tests** (1000 iterações) que validam a invariante "nenhum cliente é duplicado ou omitido" — preserve essa invariante ao mexer em crossover/mutação.

## Arquitetura

O projeto é um solucionador de **VRP (Vehicle Routing Problem)** hospitalar — múltiplos veículos saindo de um depósito central (Hospital, ID 0), com restrições de capacidade, autonomia e prioridade de entrega. Evoluiu de um solucionador TSP; resquícios do TSP ainda existem (ver abaixo). Três módulos cooperam: `tsp.py` é o driver; os outros dois são helpers puros.

### Representação genética (central para entender tudo)

Um cromossomo é uma **permutação de IDs inteiros de clientes** (`list[int]`), de `1` a `N_CITIES-1` — o depósito (ID 0) **não** aparece no cromossomo. As estruturas de dados estão em `genetic_algorithm.py`:

- `City` (dataclass frozen): `id, x, y, demand, priority`. ID 0 = depósito. `priority` 10 = medicamento crítico, 1 = insumo regular. `create_cities_from_locations` gera demanda/prioridade determinísticas quando não fornecidas.
- `FleetConfig` (dataclass frozen): `num_vehicles, vehicle_capacity, vehicle_autonomy`.
- `cities_by_id`: `dict[int, City]` passado a quase todas as funções.

A peça-chave é **`split_routes`**: converte a permutação plana em rotas por veículo, **gulosamente** — acumula clientes em um veículo até que adicionar o próximo viole capacidade OU autonomia (contando o retorno ao depósito), então abre um novo veículo. Ou seja, o número de veículos é uma *consequência* do cromossomo + restrições, não é codificado no cromossomo. `calculate_fitness` chama `split_routes` e soma: distância total + penalidade de prioridade (`priority × distância acumulada até o cliente`, punindo entregas urgentes tardias) + penalidades de capacidade/autonomia excedidas (×1000 sobre o excesso) + penalidade se o nº de rotas exceder `num_vehicles` (×5000). **Menor fitness = melhor** (é minimização).

### Módulos

- **`genetic_algorithm.py`** — primitivas do AG (todas operando sobre `list[int]`): `generate_random_population`, `split_routes`, `calculate_fitness`, `order_crossover` (OX), `mutate`, `sort_population`. `mutate` escolhe aleatoriamente entre três operadores (swap / inversion / reallocate) quando dispara. Expõe `default_problems` (conjuntos de coordenadas TSP legados, indexados por 5/10/12/15). **Não há mais bloco `__main__`** — rodar este arquivo direto não faz nada.
- **`draw_functions.py`** — renderização Pygame + truque matplotlib-sobre-pygame: `draw_plot` desenha uma figura matplotlib num canvas `Agg` off-screen e faz blit (o `matplotlib.use("Agg")` no import é necessário). Também `draw_cities` (hospital como quadrado vermelho com cruz; críticos como círculo duplo laranja; regulares azuis), `draw_paths` (uma cor por veículo, com setas de direção) e `draw_stats_panel` (dashboard da frota: carga/distância/rota e alertas por veículo).
- **`benchmark_att48.py`** — apenas dados: coordenadas do benchmark ATT de 48 cidades e a ordem ótima conhecida.

### O loop principal (`tsp.py`)

Cada iteração: pontua toda a população com `calculate_fitness`, ordena ascendente, preserva o melhor (elitismo) e repõe a população. A **seleção é por rank** (pesos `POPULATION_SIZE - i` sobre a lista ordenada) — isso é deliberado para evitar overflow quando penalidades produzem fitness gigantes, então não troque por seleção proporcional a `1/fitness` sem considerar isso. O melhor cromossomo é dividido com `split_routes` e desenhado por veículo.

**Layout da janela** (`WIDTH, HEIGHT = 1200, 500`): três faixas horizontais — gráfico de convergência matplotlib em `x < PLOT_X_OFFSET (400)`, mapa das cidades em `[PLOT_X_OFFSET, PLOT_X_OFFSET + MAP_WIDTH(550)]`, e dashboard da frota a partir de `PANEL_X (950)`. As cidades são geradas só dentro da faixa do mapa e o depósito fica no centro dela. Mexer no layout exige atualizar esses offsets em conjunto.

### Trocando a instância do problema

`tsp.py` tem três formas de inicializar `cities_locations`: geração aleatória (ativa), `default_problems[N]` (comentado) e o benchmark att48 (comentado). Para trocar, comente o bloco ativo e descomente outro — não há flag de linha de comando.

### Resquícios do TSP a observar

- `demo_crossover.py` e `demo_mutation.py` são demos **legadas e autocontidas** do TSP — definem suas próprias versões de `order_crossover`/`mutate` (operando sobre tuplas `(x,y)`) e **não** importam `genetic_algorithm`. Não as use como referência da lógica atual nem assuma que refletem o pacote.
- `default_problems` e `benchmark_att48.py` são dados de coordenadas herdados do TSP; ainda úteis como instâncias, mas não carregam demanda/prioridade.
- `draw_text` existe e funciona, mas não é chamada pelo loop atual.
- O README ainda descreve o projeto como TSP puro e está desatualizado em relação ao VRP — prefira `SPEC.md` para o comportamento pretendido.
