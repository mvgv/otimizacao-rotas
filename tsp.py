# -*- coding: utf-8 -*-
"""Módulo principal que executa o solucionador de Roteamento de Veículos (VRP) com AG.

Pergunta ao usuário as estratégias (inicialização, seleção, crossover, mutação) e se
deseja a visualização do Pygame. Roda o loop evolutivo até N_GENERATIONS e, ao final,
grava um arquivo de texto com o resultado.
"""

# 1. Biblioteca padrão
import datetime
import json
import os
import random

# 2. Bibliotecas de terceiros
import pygame
from pygame.locals import QUIT, KEYDOWN, K_q

# 3. Módulos locais
from draw_functions import draw_cities, draw_paths, draw_plot, draw_stats_panel
from genetic_algorithm import (
    City,
    FleetConfig,
    create_cities_from_locations,
    calculate_distance,
    generate_random_population,
    generate_hull_seeded_population,
    generate_nearest_neighbor_population,
    generate_sweep_population,
    generate_clarke_wright_population,
    calculate_fitness,
    split_routes,
    sort_population,
    select_parents,
    crossover,
    mutate,
)

# Estratégias de inicialização disponíveis: opção do menu -> (chave, rótulo)
INIT_STRATEGIES = {
    "1": ("random", "Aleatória (100% aleatório)"),
    "2": ("hull", "Convex Hull (inserção pelo fecho convexo)"),
    "3": ("nn", "Vizinho mais próximo (Nearest Neighbor)"),
    "4": ("sweep", "Varredura (Sweep, ângulo polar do depósito)"),
    "5": ("savings", "Clarke-Wright (Economias)"),
}

# Operadores de mutação disponíveis: opção do menu -> (chave, rótulo)
MUTATION_STRATEGIES = {
    "1": ("random", "Aleatória (sorteia entre todos)"),
    "2": ("swap", "Swap (troca dois clientes)"),
    "3": ("inversion", "Inversion (inverte subsegmento)"),
    "4": ("reallocate", "Reallocate (move um cliente)"),
    "5": ("or_opt", "Or-opt (move cadeia de 2-3 clientes)"),
    "6": ("scramble", "Scramble (embaralha subsegmento)"),
    "7": ("two_opt", "2-opt (reversão gulosa que reduz distância)"),
}

# Métodos de seleção de pais: opção do menu -> (chave, rótulo)
SELECTION_STRATEGIES = {
    "1": ("rank", "Rank (proporcional à posição no ranking)"),
    "2": ("tournament", "Torneio (k aleatórios, vence o melhor)"),
    "3": ("roulette", "Roleta (proporcional a 1/fitness)"),
}

# Operadores de crossover: opção do menu -> (chave, rótulo)
CROSSOVER_STRATEGIES = {
    "1": ("ox", "Order Crossover (OX)"),
    "2": ("pmx", "Partially Mapped Crossover (PMX)"),
    "3": ("cx", "Cycle Crossover (CX)"),
}

# Descrições legíveis para o relatório (sem jargão de algoritmo genético).
# Usadas no TXT/JSON destinados à interpretação por um especialista hospitalar.
INIT_DESCRIPTIONS = {
    "random": "Aleatória",
    "hull": "Pelo contorno geográfico das cidades",
    "nn": "Pela cidade mais próxima a cada passo",
    "sweep": "Por varredura angular a partir do hospital",
    "savings": "Pelo método das economias (Clarke-Wright)",
}
SELECTION_DESCRIPTIONS = {
    "rank": "Priorizando os melhores planos por ranking",
    "tournament": "Por disputa entre planos candidatos",
    "roulette": "Proporcional ao desempenho de cada plano",
}
CROSSOVER_DESCRIPTIONS = {
    "ox": "Preservando a ordem das visitas",
    "pmx": "Por mapeamento parcial de trechos",
    "cx": "Por recombinação de posições em ciclo",
}
MUTATION_DESCRIPTIONS = {
    "random": "Ajustes variados (combinação de técnicas)",
    "swap": "Troca de duas paradas",
    "inversion": "Inversão de um trecho da rota",
    "reallocate": "Realocação de uma parada",
    "or_opt": "Realocação de um pequeno grupo de paradas",
    "scramble": "Reorganização de um trecho da rota",
    "two_opt": "Eliminação de cruzamentos na rota",
}

# Configurações de layout da janela e visualização
WIDTH, HEIGHT = 1200, 500
PLOT_X_OFFSET = 400
MAP_WIDTH = 550
PANEL_X = 950
PANEL_WIDTH = 250
PANEL_HEIGHT = 500

NODE_RADIUS = 7
FPS = 30

# Parâmetros do Algoritmo Genético
N_CITIES = 16  # Total de cidades incluindo o Hospital (ID 0)
POPULATION_SIZE = 100
MUTATION_PROBABILITY = 0.6
N_GENERATIONS = 20000  # Limite de gerações por execução

# Cores dos veículos (RGB)
VEHICLE_COLORS = [
    (13, 110, 253),  # Azul
    (25, 135, 84),  # Verde
    (111, 66, 193),  # Roxo
    (253, 126, 20),  # Laranja
    (32, 201, 151),  # Verde-água
    (214, 51, 132),  # Rosa
]

# Configuração da Frota de Veículos
fleet = FleetConfig(
    num_vehicles=4,
    vehicle_capacity=100.0,
    vehicle_autonomy=1200.0,
)


def _choose_from(menu: dict[str, tuple[str, str]], title: str) -> str:
    """Pergunta ao usuário uma opção de um menu (chave -> (valor, rótulo)).

    Args:
        menu: Dicionário opção -> (valor retornado, rótulo exibido).
        title: Título exibido acima das opções.

    Returns:
        O valor associado à opção escolhida.
    """
    print("-" * 50)
    print(title)
    for option, (_, label) in menu.items():
        print(f"  [{option}] {label}")

    valid_options = "/".join(menu)
    while True:
        choice = input(f"Opção [{valid_options}]: ").strip()
        if choice in menu:
            return menu[choice][0]
        print(f"Opção inválida. Digite uma das opções: {valid_options}.")


def choose_initialization() -> str:
    """Pergunta ao usuário qual estratégia de inicialização usar."""
    return _choose_from(INIT_STRATEGIES, "Escolha o tipo de inicialização da população:")


def choose_selection() -> str:
    """Pergunta ao usuário qual método de seleção de pais usar."""
    return _choose_from(SELECTION_STRATEGIES, "Escolha o método de seleção de pais:")


def choose_crossover() -> str:
    """Pergunta ao usuário qual operador de crossover usar."""
    return _choose_from(CROSSOVER_STRATEGIES, "Escolha o operador de crossover:")


def choose_mutation() -> str:
    """Pergunta ao usuário qual operador de mutação usar."""
    return _choose_from(MUTATION_STRATEGIES, "Escolha o operador de mutação:")


def choose_visualization() -> bool:
    """Pergunta se o usuário quer acompanhar a execução na janela do Pygame.

    Returns:
        True para rodar com visualização; False para o modo headless.
    """
    print("-" * 50)
    print("Deseja acompanhar a execução na janela do Pygame?")
    print("  [1] Sim (com visualização)")
    print("  [2] Não (modo headless, mais rápido)")
    while True:
        choice = input("Opção [1/2]: ").strip()
        if choice == "1":
            return True
        if choice == "2":
            return False
        print("Opção inválida. Digite 1 ou 2.")


def build_cities() -> tuple[dict[int, City], list[int]]:
    """Gera a instância do problema: Hospital no centro + clientes aleatórios.

    Returns:
        Tupla (cities_by_id, cities_ids), onde cities_ids exclui o depósito 0.
    """
    depot_x = PLOT_X_OFFSET + MAP_WIDTH // 2
    depot_y = HEIGHT // 2
    cities_locations = [(depot_x, depot_y)]
    for _ in range(N_CITIES - 1):
        cities_locations.append(
            (
                random.randint(PLOT_X_OFFSET + 30, PLOT_X_OFFSET + MAP_WIDTH - 30),
                random.randint(30, HEIGHT - 30),
            )
        )

    # Alternativas (descomente uma): default_problems[15] ou o benchmark att48.
    cities_by_id = create_cities_from_locations(cities_locations)
    cities_ids = list(range(1, N_CITIES))
    return cities_by_id, cities_ids


def build_initial_population(
    init_strategy: str,
    cities_ids: list[int],
    cities_by_id: dict[int, City],
) -> list[list[int]]:
    """Cria a população inicial conforme a estratégia escolhida."""
    if init_strategy == "hull":
        return generate_hull_seeded_population(cities_ids, cities_by_id, POPULATION_SIZE)
    if init_strategy == "nn":
        return generate_nearest_neighbor_population(
            cities_ids, cities_by_id, POPULATION_SIZE
        )
    if init_strategy == "sweep":
        return generate_sweep_population(cities_ids, cities_by_id, POPULATION_SIZE)
    if init_strategy == "savings":
        return generate_clarke_wright_population(
            cities_ids, cities_by_id, fleet, POPULATION_SIZE
        )
    return generate_random_population(cities_ids, POPULATION_SIZE)


def route_stats(route: list[int], cities_by_id: dict[int, City]) -> tuple[float, float]:
    """Calcula (carga, distância) de uma rota individual, fechando no depósito."""
    depot = cities_by_id[0]
    load = 0.0
    dist = 0.0
    last = depot
    for cid in route:
        city = cities_by_id[cid]
        dist += calculate_distance((last.x, last.y), (city.x, city.y))
        load += city.demand
        last = city
    dist += calculate_distance((last.x, last.y), (depot.x, depot.y))
    return load, dist


def _should_quit() -> bool:
    """Verifica eventos do Pygame; True se o usuário pediu para sair (QUIT ou Q)."""
    for event in pygame.event.get():
        if event.type == QUIT:
            return True
        if event.type == KEYDOWN and event.key == K_q:
            return True
    return False


def _draw_generation(
    screen: pygame.Surface,
    clock: pygame.time.Clock,
    cities_by_id: dict[int, City],
    best_solution: list[int],
    best_fitness_values: list[float],
) -> None:
    """Renderiza uma geração: gráfico de convergência, mapa, rotas e dashboard."""
    screen.fill((248, 249, 250))
    draw_plot(screen, list(range(1, len(best_fitness_values) + 1)), best_fitness_values)
    draw_cities(screen, cities_by_id, NODE_RADIUS)

    best_routes = split_routes(best_solution, cities_by_id, fleet)
    draw_paths(screen, best_routes, cities_by_id, VEHICLE_COLORS)
    draw_stats_panel(
        screen,
        best_routes,
        cities_by_id,
        fleet,
        VEHICLE_COLORS,
        panel_x=PANEL_X,
        panel_y=0,
        panel_width=PANEL_WIDTH,
        panel_height=PANEL_HEIGHT,
    )
    pygame.display.flip()
    clock.tick(FPS)


def run_evolution(
    cities_by_id: dict[int, City],
    cities_ids: list[int],
    *,
    init_strategy: str,
    selection_strategy: str,
    crossover_strategy: str,
    mutation_strategy: str,
    visualize: bool,
) -> tuple[list[int], float, list[float], int]:
    """Executa o AG por até N_GENERATIONS, com ou sem visualização.

    Returns:
        Tupla (melhor_solução, melhor_fitness, histórico_de_fitness, gerações_rodadas).
    """
    population = build_initial_population(init_strategy, cities_ids, cities_by_id)
    best_fitness_values: list[float] = []
    best_solution = population[0]
    best_fitness = float("inf")

    screen = None
    clock = None
    if visualize:
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(
            f"VRP | Init:{init_strategy} | Sel:{selection_strategy} | "
            f"Cross:{crossover_strategy} | Mut:{mutation_strategy}"
        )
        clock = pygame.time.Clock()

    generation = 0
    for generation in range(1, N_GENERATIONS + 1):
        if visualize and _should_quit():
            break

        population_fitness = [
            calculate_fitness(ind, cities_by_id, fleet) for ind in population
        ]
        population, population_fitness = sort_population(population, population_fitness)
        best_fitness = population_fitness[0]
        best_solution = population[0]
        best_fitness_values.append(best_fitness)

        if visualize and screen is not None and clock is not None:
            _draw_generation(
                screen, clock, cities_by_id, best_solution, best_fitness_values
            )
        elif not visualize and (generation == 1 or generation % 200 == 0):
            print(
                f"Geração {generation}/{N_GENERATIONS}: "
                f"Melhor Custo = {round(best_fitness, 2)}"
            )

        # Reprodução com elitismo (pulada na última geração, sem efeito)
        if generation < N_GENERATIONS:
            new_population = [population[0]]
            while len(new_population) < POPULATION_SIZE:
                parent1, parent2 = select_parents(
                    population, population_fitness, method=selection_strategy
                )
                child = crossover(parent1, parent2, method=crossover_strategy)
                child = mutate(
                    child,
                    MUTATION_PROBABILITY,
                    operator=mutation_strategy,
                    cities_by_id=cities_by_id,
                )
                new_population.append(child)
            population = new_population

    if visualize:
        pygame.quit()

    return best_solution, best_fitness, best_fitness_values, generation


def write_results(
    cities_by_id: dict[int, City],
    best_solution: list[int],
    best_fitness: float,
    best_fitness_values: list[float],
    generations_run: int,
    config: dict[str, str],
) -> str:
    """Grava um arquivo de texto com o resumo do resultado e retorna o caminho."""
    now = datetime.datetime.now()
    results_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "resultados"
    )
    os.makedirs(results_dir, exist_ok=True)
    filename = os.path.join(results_dir, f"resultado_{now:%Y%m%d_%H%M%S}.txt")

    routes = split_routes(best_solution, cities_by_id, fleet)
    initial_cost = round(best_fitness_values[0], 2) if best_fitness_values else None

    # Mapeia cada cliente ao veículo e à ordem de visita dentro da rota
    assignment: dict[int, tuple[int, int]] = {}
    for v_idx, route in enumerate(routes, start=1):
        for pos, cid in enumerate(route, start=1):
            assignment[cid] = (v_idx, pos)

    def priority_label(priority: int) -> str:
        if priority >= 10:
            return "crítico"
        if priority <= 0:
            return "depósito"
        return "regular"

    depot = cities_by_id[0]
    client_ids = [cid for cid in sorted(cities_by_id) if cid != 0]
    total_demand = sum(cities_by_id[c].demand for c in client_ids)
    total_distance = sum(route_stats(r, cities_by_id)[1] for r in routes)
    num_critical = sum(1 for c in client_ids if cities_by_id[c].priority >= 10)

    lines = [
        "=" * 60,
        "PLANO DE ROTAS DE ENTREGA HOSPITALAR",
        "=" * 60,
        f"Data/hora: {now:%Y-%m-%d %H:%M:%S}",
        "",
        "LEGENDA (unidades e termos)",
        "  - Deposito = Hospital, sempre a cidade de ID 0; toda rota comeca e",
        "    termina nele.",
        "  - Coordenadas (x, y) em pixels; distancias sao euclidianas em pixels.",
        "  - Demanda = carga a ser entregue na cidade (unidades).",
        "  - Prioridade: 10 = medicamento critico (urgente); 1 = insumo regular.",
        "  - Custo logistico = indice que combina a distancia total percorrida e",
        "    penalidades por violar restricoes (capacidade dos veiculos, autonomia",
        "    e atraso de entregas urgentes). Quanto MENOR, melhor o plano.",
        "  - Status da rota: OK; SOBRECARGA (excede capacidade); ou AUTONOMIA",
        "    EXCEDIDA (excede a distancia maxima do veiculo).",
        "",
        "MÉTODO DE PLANEJAMENTO",
        "  Abordagem: otimização por melhoria iterativa das rotas.",
        f"  Construção inicial das rotas : {INIT_DESCRIPTIONS.get(config['init'], config['init'])}",
        f"  Estratégia de seleção        : {SELECTION_DESCRIPTIONS.get(config['selection'], config['selection'])}",
        f"  Forma de recombinação        : {CROSSOVER_DESCRIPTIONS.get(config['crossover'], config['crossover'])}",
        f"  Ajuste local de rota         : {MUTATION_DESCRIPTIONS.get(config['mutation'], config['mutation'])}",
        f"  Planos avaliados por ciclo   : {POPULATION_SIZE}",
        f"  Intensidade de ajuste local  : {MUTATION_PROBABILITY}",
        f"  Ciclos de refinamento        : {generations_run} (limite {N_GENERATIONS})",
        "",
        "FROTA",
        f"  Veículos disponíveis : {fleet.num_vehicles}",
        f"  Veículos utilizados  : {len(routes)}",
        f"  Capacidade/veículo   : {fleet.vehicle_capacity}",
        f"  Autonomia/veículo    : {fleet.vehicle_autonomy}",
        "",
        "DEPÓSITO (HOSPITAL)",
        f"  Cidade 0 em (x={depot.x}, y={depot.y})",
        "",
        f"CIDADES / CLIENTES ({len(client_ids)} no total, {num_critical} críticos)",
        "  ID | tipo     | x    | y    | demanda | prioridade | veículo | ordem",
    ]

    for cid in client_ids:
        c = cities_by_id[cid]
        v_idx, pos = assignment.get(cid, (0, 0))
        veh = f"V{v_idx}" if v_idx else "-"
        ordem = str(pos) if pos else "-"
        lines.append(
            f"  {cid:>2} | {priority_label(c.priority):<8} | {c.x:<4} | {c.y:<4} | "
            f"{c.demand:>7.1f} | {c.priority:>10} | {veh:>7} | {ordem:>5}"
        )

    lines += [
        "",
        "RESUMO DO PLANO",
        f"  Custo logístico do plano inicial : {initial_cost}",
        f"  Custo logístico do plano final   : {round(best_fitness, 2)}",
        f"  Distância total percorrida       : {total_distance:.1f}",
        f"  Carga total entregue             : {total_demand:.1f}",
        f"  Veículos utilizados              : {len(routes)} / {fleet.num_vehicles}",
        "",
        "ROTAS DETALHADAS",
    ]

    for i, route in enumerate(routes, start=1):
        load, dist = route_stats(route, cities_by_id)
        alerts = []
        if load > fleet.vehicle_capacity:
            alerts.append("SOBRECARGA")
        if dist > fleet.vehicle_autonomy:
            alerts.append("AUTONOMIA EXCEDIDA")
        status = ", ".join(alerts) if alerts else "OK"
        criticos = [cid for cid in route if cities_by_id[cid].priority >= 10]
        seq = "0 -> " + " -> ".join(map(str, route)) + " -> 0"

        lines.append(f"  Veículo {i}:")
        lines.append(f"    Rota          : {seq}")
        lines.append(f"    Paradas       : {len(route)} cidades {route}")
        lines.append(
            f"    Carga         : {load:.1f}/{fleet.vehicle_capacity:.0f}"
            f" (folga {fleet.vehicle_capacity - load:.1f})"
        )
        lines.append(
            f"    Distância     : {dist:.1f}/{fleet.vehicle_autonomy:.0f}"
            f" (folga {fleet.vehicle_autonomy - dist:.1f})"
        )
        lines.append(f"    Críticos      : {criticos if criticos else 'nenhum'}")
        lines.append(f"    Status        : {status}")

    lines += [
        "",
        f"SEQUÊNCIA GERAL DE ENTREGAS (ordem consolidada das cidades): {best_solution}",
        "",
    ]

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filename


def build_result_data(
    cities_by_id: dict[int, City],
    best_solution: list[int],
    best_fitness: float,
    best_fitness_values: list[float],
    generations_run: int,
    config: dict[str, str],
) -> dict:
    """Monta um dicionário estruturado com todo o resultado (cidades, frota, rotas).

    Serve de fonte para a saída JSON, autocontida o suficiente para uma LLM
    responder perguntas sobre cidades, veículos e rotas.
    """
    routes = split_routes(best_solution, cities_by_id, fleet)

    assignment: dict[int, tuple[int, int]] = {}
    for v_idx, route in enumerate(routes, start=1):
        for pos, cid in enumerate(route, start=1):
            assignment[cid] = (v_idx, pos)

    def priority_label(priority: int) -> str:
        if priority >= 10:
            return "crítico"
        if priority <= 0:
            return "depósito"
        return "regular"

    depot = cities_by_id[0]
    client_ids = [cid for cid in sorted(cities_by_id) if cid != 0]
    total_distance = sum(route_stats(r, cities_by_id)[1] for r in routes)
    total_demand = sum(cities_by_id[c].demand for c in client_ids)

    cities_data = []
    for cid in client_ids:
        c = cities_by_id[cid]
        v_idx, pos = assignment.get(cid, (0, 0))
        cities_data.append(
            {
                "id": cid,
                "tipo": priority_label(c.priority),
                "x": c.x,
                "y": c.y,
                "demanda": c.demand,
                "prioridade": c.priority,
                "veiculo": v_idx or None,
                "ordem_visita": pos or None,
            }
        )

    routes_data = []
    for i, route in enumerate(routes, start=1):
        load, dist = route_stats(route, cities_by_id)
        alerts = []
        if load > fleet.vehicle_capacity:
            alerts.append("SOBRECARGA")
        if dist > fleet.vehicle_autonomy:
            alerts.append("AUTONOMIA EXCEDIDA")
        routes_data.append(
            {
                "veiculo": i,
                "sequencia": [0] + route + [0],
                "cidades": route,
                "paradas": len(route),
                "carga": round(load, 2),
                "capacidade": fleet.vehicle_capacity,
                "folga_carga": round(fleet.vehicle_capacity - load, 2),
                "distancia": round(dist, 2),
                "autonomia": fleet.vehicle_autonomy,
                "folga_distancia": round(fleet.vehicle_autonomy - dist, 2),
                "cidades_criticas": [
                    cid for cid in route if cities_by_id[cid].priority >= 10
                ],
                "status": alerts or ["OK"],
            }
        )

    return {
        "metadata": {
            "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "problema": "Planejamento de rotas de entrega hospitalar",
            "unidades": {
                "coordenadas": "pixels",
                "distancia": "pixels (euclidiana)",
                "demanda": "unidades de carga",
            },
            "legenda": {
                "deposito": "Hospital (cidade de ID 0); toda rota começa e termina nele",
                "prioridade": {
                    "10": "medicamento crítico (urgente)",
                    "1": "insumo regular",
                },
                "custo_logistico": (
                    "índice que combina a distância total percorrida e penalidades "
                    "por violar restrições (capacidade dos veículos, autonomia e "
                    "atraso de entregas urgentes); quanto menor, melhor o plano"
                ),
                "status": "OK, SOBRECARGA (excede capacidade) ou AUTONOMIA EXCEDIDA",
            },
        },
        "metodo_planejamento": {
            "abordagem": "otimização por melhoria iterativa das rotas",
            "construcao_inicial": INIT_DESCRIPTIONS.get(config["init"], config["init"]),
            "estrategia_selecao": SELECTION_DESCRIPTIONS.get(
                config["selection"], config["selection"]
            ),
            "forma_recombinacao": CROSSOVER_DESCRIPTIONS.get(
                config["crossover"], config["crossover"]
            ),
            "ajuste_local": MUTATION_DESCRIPTIONS.get(
                config["mutation"], config["mutation"]
            ),
            "planos_avaliados_por_ciclo": POPULATION_SIZE,
            "intensidade_ajuste_local": MUTATION_PROBABILITY,
            "ciclos_refinamento": generations_run,
            "ciclos_refinamento_limite": N_GENERATIONS,
        },
        "frota": {
            "veiculos_disponiveis": fleet.num_vehicles,
            "veiculos_utilizados": len(routes),
            "capacidade_por_veiculo": fleet.vehicle_capacity,
            "autonomia_por_veiculo": fleet.vehicle_autonomy,
        },
        "deposito": {"id": 0, "x": depot.x, "y": depot.y},
        "cidades": cities_data,
        "resumo": {
            "custo_plano_inicial": (
                round(best_fitness_values[0], 2) if best_fitness_values else None
            ),
            "custo_plano_final": round(best_fitness, 2),
            "distancia_total": round(total_distance, 2),
            "carga_total_entregue": round(total_demand, 2),
            "veiculos_utilizados": len(routes),
        },
        "rotas": routes_data,
        "sequencia_geral_entregas": list(best_solution),
    }


def write_results_json(data: dict, txt_path: str) -> str:
    """Grava o resultado estruturado em JSON, pareado ao txt (mesmo nome base)."""
    json_path = os.path.splitext(txt_path)[0] + ".json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return json_path


def main() -> None:
    """Orquestra a execução: prompts, evolução e gravação do resultado."""
    print("=" * 50)
    print("Otimizador de Rotas Hospitalar (VRP) - Algoritmo Genético")
    print("=" * 50)

    cities_by_id, cities_ids = build_cities()

    init_strategy = choose_initialization()
    selection_strategy = choose_selection()
    crossover_strategy = choose_crossover()
    mutation_strategy = choose_mutation()
    visualize = choose_visualization()

    print("=" * 50)
    print(
        f"Configuração: init={init_strategy}, seleção={selection_strategy}, "
        f"crossover={crossover_strategy}, mutação={mutation_strategy}, "
        f"visualização={'sim' if visualize else 'não'}"
    )
    print(f"Rodando até {N_GENERATIONS} gerações...")
    print("=" * 50)

    best_solution, best_fitness, best_fitness_values, generations_run = run_evolution(
        cities_by_id,
        cities_ids,
        init_strategy=init_strategy,
        selection_strategy=selection_strategy,
        crossover_strategy=crossover_strategy,
        mutation_strategy=mutation_strategy,
        visualize=visualize,
    )

    config = {
        "init": init_strategy,
        "selection": selection_strategy,
        "crossover": crossover_strategy,
        "mutation": mutation_strategy,
    }
    filepath = write_results(
        cities_by_id,
        best_solution,
        best_fitness,
        best_fitness_values,
        generations_run,
        config,
    )
    data = build_result_data(
        cities_by_id,
        best_solution,
        best_fitness,
        best_fitness_values,
        generations_run,
        config,
    )
    json_path = write_results_json(data, filepath)

    print(
        f"\nConcluído em {generations_run} gerações. "
        f"Melhor custo: {round(best_fitness, 2)}"
    )
    print(f"Resultado (TXT)  gravado em: {filepath}")
    print(f"Resultado (JSON) gravado em: {json_path}")


if __name__ == "__main__":
    main()
