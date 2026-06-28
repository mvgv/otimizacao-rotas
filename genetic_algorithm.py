# -*- coding: utf-8 -*-
"""Módulo de Algoritmo Genético para o Problema de Roteamento de Veículos (VRP).

Este módulo contém as estruturas de dados e as operações básicas do AG,
incluindo geração de população, cruzamento, mutação, cálculo de fitness e
divisão de rotas.
"""

# 1. Biblioteca padrão
import math
import random
from dataclasses import dataclass
from typing import Optional, Sequence

# Dicionários de problemas padrão de TSP legados (coordenadas x, y)
default_problems = {
    5: [(733, 251), (706, 87), (546, 97), (562, 49), (576, 253)],
    10: [
        (470, 169),
        (602, 202),
        (754, 239),
        (476, 233),
        (468, 301),
        (522, 29),
        (597, 171),
        (487, 325),
        (746, 232),
        (558, 136),
    ],
    12: [
        (728, 67),
        (560, 160),
        (602, 312),
        (712, 148),
        (535, 340),
        (720, 354),
        (568, 300),
        (629, 260),
        (539, 46),
        (634, 343),
        (491, 135),
        (768, 161),
    ],
    15: [
        (512, 317),
        (741, 72),
        (552, 50),
        (772, 346),
        (637, 12),
        (589, 131),
        (732, 165),
        (605, 15),
        (730, 38),
        (576, 216),
        (589, 381),
        (711, 387),
        (563, 228),
        (494, 22),
        (787, 288),
    ],
}


@dataclass(frozen=True)
class City:
    """Representa uma cidade ou ponto de entrega hospitalar.

    Attributes:
        id: Identificador único da cidade (0 é o depósito/hospital).
        x: Coordenada X.
        y: Coordenada Y.
        demand: Demanda de carga (peso/volume) de medicamentos ou insumos.
        priority: Nível de prioridade (ex: 1 para insumos, 10 para medicamentos críticos).
    """

    id: int
    x: int
    y: int
    demand: float
    priority: int


@dataclass(frozen=True)
class FleetConfig:
    """Configurações da frota de veículos disponíveis.

    Attributes:
        num_vehicles: Quantidade máxima de veículos na frota.
        vehicle_capacity: Capacidade de carga útil de cada veículo.
        vehicle_autonomy: Distância máxima que cada veículo pode percorrer.
    """

    num_vehicles: int
    vehicle_capacity: float
    vehicle_autonomy: float


def create_cities_from_locations(
    locations: list[tuple[int, int]],
    demands: Optional[list[float]] = None,
    priorities: Optional[list[int]] = None,
) -> dict[int, City]:
    """Cria um dicionário de objetos City a partir de coordenadas brutas.

    O primeiro elemento (índice 0) é considerado o Hospital (Depósito).

    Args:
        locations: Lista de coordenadas (x, y).
        demands: Lista opcional de demandas de carga.
        priorities: Lista opcional de prioridades.

    Returns:
        Dicionário mapeando ID de cidade para objeto City.
    """
    cities: dict[int, City] = {}
    depot_loc = locations[0]
    cities[0] = City(id=0, x=depot_loc[0], y=depot_loc[1], demand=0.0, priority=0)

    for i, loc in enumerate(locations[1:], start=1):
        # Gera demandas e prioridades determinísticas caso não fornecidas
        demand = (
            demands[i] if (demands and i < len(demands)) else float((i * 7) % 26 + 5)
        )
        priority = (
            priorities[i]
            if (priorities and i < len(priorities))
            else (10 if i % 3 == 0 else 1)
        )
        cities[i] = City(id=i, x=loc[0], y=loc[1], demand=demand, priority=priority)

    return cities


def calculate_distance(
    point1: tuple[float, float], point2: tuple[float, float]
) -> float:
    """Calcula a distância euclidiana entre dois pontos.

    Args:
        point1: Tupla com coordenadas (x, y) do ponto 1.
        point2: Tupla com coordenadas (x, y) do ponto 2.

    Returns:
        Distância euclidiana como float.
    """
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)


def split_routes(
    chromosome: list[int],
    cities_by_id: dict[int, City],
    fleet: FleetConfig,
) -> list[list[int]]:
    """Divide um cromossomo (permutação de cidades) em rotas para múltiplos veículos.

    O particionamento é feito de forma gulosa. Um veículo atende as cidades na sequência
    do cromossomo até que a inclusão da próxima cidade viole a sua capacidade de carga
    ou sua autonomia limite de distância (considerando o retorno ao hospital).

    Args:
        chromosome: Lista com a permutação de IDs das cidades (excluindo depósito 0).
        cities_by_id: Dicionário indexado de cidades (ID -> City).
        fleet: Configuração de capacidade e autonomia dos veículos.

    Returns:
        Lista de rotas, onde cada rota é uma lista de IDs de cidades.
    """
    routes: list[list[int]] = []
    if not chromosome:
        return routes

    depot = cities_by_id[0]
    current_route: list[int] = []
    current_load = 0.0
    current_dist = 0.0
    last_city = depot

    for city_id in chromosome:
        city = cities_by_id[city_id]
        dist_to_city = calculate_distance((last_city.x, last_city.y), (city.x, city.y))
        dist_to_depot = calculate_distance((city.x, city.y), (depot.x, depot.y))

        # Verifica restrições
        exceeds_capacity = current_load + city.demand > fleet.vehicle_capacity
        exceeds_autonomy = (
            current_dist + dist_to_city + dist_to_depot > fleet.vehicle_autonomy
        )

        if (exceeds_capacity or exceeds_autonomy) and current_route:
            routes.append(current_route)
            current_route = [city_id]
            current_load = city.demand
            current_dist = calculate_distance((depot.x, depot.y), (city.x, city.y))
            last_city = city
        else:
            current_route.append(city_id)
            current_load += city.demand
            current_dist += dist_to_city
            last_city = city

    if current_route:
        routes.append(current_route)

    return routes


def calculate_fitness(
    chromosome: list[int],
    cities_by_id: dict[int, City],
    fleet: FleetConfig,
) -> float:
    """Calcula o custo total da solução (fitness) a ser minimizado.

    O custo inclui:
    1. Distância total percorrida de todas as rotas de veículos.
    2. Penalidade de prioridade (tempo de espera/distância percorrida até
       as cidades que demandam medicamentos críticos).
    3. Penalidade por exceder capacidade de carga útil individual.
    4. Penalidade por exceder a autonomia máxima individual do veículo.
    5. Penalidade pesada caso o número de rotas necessárias exceda a frota.

    Args:
        chromosome: Lista com a permutação de IDs das cidades.
        cities_by_id: Dicionário indexado de cidades (ID -> City).
        fleet: Configuração de capacidade e autonomia dos veículos.

    Returns:
        Valor de aptidão (fitness). Menor é melhor.
    """
    if not chromosome:
        return float("inf")

    routes = split_routes(chromosome, cities_by_id, fleet)
    depot = cities_by_id[0]

    total_distance = 0.0
    priority_penalty = 0.0
    capacity_penalty = 0.0
    autonomy_penalty = 0.0

    for route in routes:
        route_load = 0.0
        route_dist = 0.0
        last_city = depot

        for city_id in route:
            city = cities_by_id[city_id]
            dist_to_city = calculate_distance(
                (last_city.x, last_city.y), (city.x, city.y)
            )
            route_dist += dist_to_city
            route_load += city.demand

            # Pune entregas com prioridade alta que ocorrem no fim da rota
            priority_penalty += city.priority * route_dist
            last_city = city

        # Retorno ao depósito
        dist_to_depot = calculate_distance(
            (last_city.x, last_city.y), (depot.x, depot.y)
        )
        route_dist += dist_to_depot
        total_distance += route_dist

        # Calcula violações individuais
        if route_load > fleet.vehicle_capacity:
            capacity_penalty += (route_load - fleet.vehicle_capacity) * 1000.0
        if route_dist > fleet.vehicle_autonomy:
            autonomy_penalty += (route_dist - fleet.vehicle_autonomy) * 1000.0

    # Penalidade por extrapolar o número máximo de veículos na frota
    fleet_size_penalty = 0.0
    if len(routes) > fleet.num_vehicles:
        fleet_size_penalty += (len(routes) - fleet.num_vehicles) * 5000.0

    return (
        total_distance
        + priority_penalty
        + capacity_penalty
        + autonomy_penalty
        + fleet_size_penalty
    )


def generate_random_population(
    cities_ids: list[int], population_size: int
) -> list[list[int]]:
    """Gera uma população inicial aleatória de cromossomos (permutações).

    Args:
        cities_ids: Lista de IDs das cidades disponíveis (excluindo depósito 0).
        population_size: Quantidade de indivíduos na população.

    Returns:
        Lista de cromossomos (cada cromossomo é uma lista de IDs).
    """
    return [random.sample(cities_ids, len(cities_ids)) for _ in range(population_size)]


def convex_hull(points: Sequence[tuple[float, float]]) -> list[int]:
    """Calcula o fecho convexo (convex hull) de um conjunto de pontos 2D.

    Usa o algoritmo de cadeia monótona de Andrew (monotone chain), que ordena os
    pontos e constrói as cadeias inferior e superior em O(n log n). Pontos
    colineares nas arestas do fecho são descartados (mantém só os vértices).

    Args:
        points: Lista de coordenadas (x, y).

    Returns:
        Índices (na lista de entrada) dos vértices do fecho, em ordem anti-horária.
    """
    n = len(points)
    if n < 3:
        return list(range(n))

    order = sorted(range(n), key=lambda i: (points[i][0], points[i][1]))

    def cross(o: int, a: int, b: int) -> float:
        """Produto vetorial (z) de (a-o) x (b-o). >0 vira à esquerda."""
        return (points[a][0] - points[o][0]) * (points[b][1] - points[o][1]) - (
            points[a][1] - points[o][1]
        ) * (points[b][0] - points[o][0])

    lower: list[int] = []
    for i in order:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], i) <= 0:
            lower.pop()
        lower.append(i)

    upper: list[int] = []
    for i in reversed(order):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], i) <= 0:
            upper.pop()
        upper.append(i)

    # Remove o último ponto de cada cadeia (repetido no início da outra)
    return lower[:-1] + upper[:-1]


def hull_insertion_tour(
    cities_by_id: dict[int, City],
    client_ids: list[int],
) -> list[int]:
    """Constrói uma rota-base de clientes pela heurística de inserção pelo hull.

    Começa com os clientes que formam o fecho convexo (na ordem do hull) e insere
    os clientes interiores um a um, sempre na posição de menor aumento de distância
    (cheapest insertion). Não envolve o depósito — o resultado é uma ordenação de
    clientes que `split_routes` posteriormente particiona em veículos.

    Args:
        cities_by_id: Dicionário ID -> City (deve conter todos os client_ids).
        client_ids: IDs dos clientes a serem ordenados (sem o depósito 0).

    Returns:
        Lista de IDs de clientes formando a rota-base.
    """
    if len(client_ids) <= 3:
        return list(client_ids)

    points = [(cities_by_id[cid].x, cities_by_id[cid].y) for cid in client_ids]
    hull_indices = convex_hull(points)
    tour = [client_ids[i] for i in hull_indices]

    in_tour = set(tour)
    remaining = [cid for cid in client_ids if cid not in in_tour]

    while remaining:
        best_city: Optional[int] = None
        best_pos = 0
        best_increase = float("inf")

        for cid in remaining:
            city = cities_by_id[cid]
            for pos in range(len(tour)):
                a = cities_by_id[tour[pos]]
                b = cities_by_id[tour[(pos + 1) % len(tour)]]
                increase = (
                    calculate_distance((a.x, a.y), (city.x, city.y))
                    + calculate_distance((city.x, city.y), (b.x, b.y))
                    - calculate_distance((a.x, a.y), (b.x, b.y))
                )
                if increase < best_increase:
                    best_increase = increase
                    best_city = cid
                    best_pos = pos + 1

        assert best_city is not None
        tour.insert(best_pos, best_city)
        remaining.remove(best_city)

    return tour


def seed_population_from_tour(
    base_tour: list[int],
    client_ids: list[int],
    population_size: int,
    random_fraction: float = 0.3,
) -> list[list[int]]:
    """Monta uma população inicial a partir de uma rota-base construtiva.

    Combina três fontes para equilibrar qualidade inicial e diversidade:
    1. A própria rota-base (um indivíduo).
    2. Variantes mutadas da rota-base (preenchem a maior parte).
    3. Uma fração de indivíduos puramente aleatórios (mantém diversidade).

    Args:
        base_tour: Ordenação de clientes produzida por uma heurística construtiva.
        client_ids: IDs dos clientes (sem o depósito 0).
        population_size: Quantidade de indivíduos na população.
        random_fraction: Fração da população gerada aleatoriamente (0.0 a 1.0).

    Returns:
        Lista de cromossomos (cada um é uma permutação de client_ids).
    """
    population: list[list[int]] = [list(base_tour)]

    num_random = int((population_size - 1) * random_fraction)
    num_mutated = population_size - 1 - num_random

    for _ in range(num_mutated):
        variant = list(base_tour)
        for _ in range(random.randint(1, 3)):
            variant = mutate(variant, 1.0)
        population.append(variant)

    for _ in range(num_random):
        population.append(random.sample(client_ids, len(client_ids)))

    return population


def generate_hull_seeded_population(
    client_ids: list[int],
    cities_by_id: dict[int, City],
    population_size: int,
    random_fraction: float = 0.3,
) -> list[list[int]]:
    """Gera uma população inicial semeada pela heurística do convex hull.

    Args:
        client_ids: IDs dos clientes (sem o depósito 0).
        cities_by_id: Dicionário ID -> City.
        population_size: Quantidade de indivíduos na população.
        random_fraction: Fração da população gerada aleatoriamente (0.0 a 1.0).

    Returns:
        Lista de cromossomos (cada um é uma permutação de client_ids).
    """
    base_tour = hull_insertion_tour(cities_by_id, client_ids)
    return seed_population_from_tour(
        base_tour, client_ids, population_size, random_fraction
    )


def nearest_neighbor_tour(
    cities_by_id: dict[int, City],
    client_ids: list[int],
    start_id: Optional[int] = None,
) -> list[int]:
    """Constrói uma rota pela heurística do vizinho mais próximo.

    Parte do depósito (ou de start_id, quando informado) e, a cada passo, visita o
    cliente ainda não visitado mais próximo do último ponto visitado.

    Args:
        cities_by_id: Dicionário ID -> City.
        client_ids: IDs dos clientes a ordenar (sem o depósito 0).
        start_id: Cliente inicial opcional; se None, parte do depósito.

    Returns:
        Lista de IDs de clientes formando a rota.
    """
    if not client_ids:
        return []

    unvisited = set(client_ids)
    tour: list[int] = []

    if start_id is not None and start_id in unvisited:
        last = cities_by_id[start_id]
        tour.append(start_id)
        unvisited.remove(start_id)
    else:
        last = cities_by_id[0]

    while unvisited:
        nearest: Optional[int] = None
        best = float("inf")
        for cid in unvisited:
            city = cities_by_id[cid]
            dist = calculate_distance((last.x, last.y), (city.x, city.y))
            if dist < best:
                best = dist
                nearest = cid

        assert nearest is not None
        tour.append(nearest)
        unvisited.remove(nearest)
        last = cities_by_id[nearest]

    return tour


def sweep_tour(
    cities_by_id: dict[int, City],
    client_ids: list[int],
) -> list[int]:
    """Constrói uma rota pela heurística da varredura (sweep).

    Ordena os clientes pelo ângulo polar em torno do depósito, como um radar girando.

    Args:
        cities_by_id: Dicionário ID -> City.
        client_ids: IDs dos clientes a ordenar (sem o depósito 0).

    Returns:
        Lista de IDs de clientes ordenados por ângulo.
    """
    depot = cities_by_id[0]
    return sorted(
        client_ids,
        key=lambda cid: math.atan2(
            cities_by_id[cid].y - depot.y, cities_by_id[cid].x - depot.x
        ),
    )


def clarke_wright_tour(
    cities_by_id: dict[int, City],
    client_ids: list[int],
    fleet: FleetConfig,
) -> list[int]:
    """Constrói rotas pela heurística das economias de Clarke-Wright e as concatena.

    Começa com uma rota dedicada por cliente (depósito -> cliente -> depósito) e
    mescla iterativamente os pares com maior economia
    `s(i, j) = d(0, i) + d(0, j) - d(i, j)`, respeitando a capacidade do veículo e
    só unindo clientes que estão nas extremidades das suas rotas. As rotas finais
    são concatenadas numa única ordenação (o cromossomo), que `split_routes`
    reparticiona depois.

    Args:
        cities_by_id: Dicionário ID -> City.
        client_ids: IDs dos clientes a ordenar (sem o depósito 0).
        fleet: Configuração da frota (usa a capacidade para limitar as mesclagens).

    Returns:
        Lista de IDs de clientes formando a rota-base.
    """
    if len(client_ids) <= 1:
        return list(client_ids)

    def dist(a_id: int, b_id: int) -> float:
        a = cities_by_id[a_id]
        b = cities_by_id[b_id]
        return calculate_distance((a.x, a.y), (b.x, b.y))

    routes: dict[int, list[int]] = {cid: [cid] for cid in client_ids}
    route_of: dict[int, int] = {cid: cid for cid in client_ids}
    load: dict[int, float] = {cid: cities_by_id[cid].demand for cid in client_ids}

    savings: list[tuple[float, int, int]] = []
    for i in range(len(client_ids)):
        for j in range(i + 1, len(client_ids)):
            a, b = client_ids[i], client_ids[j]
            savings.append((dist(0, a) + dist(0, b) - dist(a, b), a, b))
    savings.sort(reverse=True)

    for _, a, b in savings:
        ra, rb = route_of[a], route_of[b]
        if ra == rb:
            continue
        if load[ra] + load[rb] > fleet.vehicle_capacity:
            continue

        route_a, route_b = routes[ra], routes[rb]
        # Só é possível mesclar se a e b estiverem nas pontas das respectivas rotas
        merged: Optional[list[int]] = None
        if route_a[-1] == a and route_b[0] == b:
            merged = route_a + route_b
        elif route_a[0] == a and route_b[-1] == b:
            merged = route_b + route_a
        elif route_a[-1] == a and route_b[-1] == b:
            merged = route_a + route_b[::-1]
        elif route_a[0] == a and route_b[0] == b:
            merged = route_a[::-1] + route_b

        if merged is None:
            continue

        routes[ra] = merged
        load[ra] += load[rb]
        del routes[rb]
        for cid in route_b:
            route_of[cid] = ra

    tour: list[int] = []
    for route in routes.values():
        tour.extend(route)
    return tour


def generate_nearest_neighbor_population(
    client_ids: list[int],
    cities_by_id: dict[int, City],
    population_size: int,
    random_fraction: float = 0.3,
) -> list[list[int]]:
    """Gera uma população inicial semeada pela heurística do vizinho mais próximo.

    Args:
        client_ids: IDs dos clientes (sem o depósito 0).
        cities_by_id: Dicionário ID -> City.
        population_size: Quantidade de indivíduos na população.
        random_fraction: Fração da população gerada aleatoriamente (0.0 a 1.0).

    Returns:
        Lista de cromossomos (cada um é uma permutação de client_ids).
    """
    base_tour = nearest_neighbor_tour(cities_by_id, client_ids)
    return seed_population_from_tour(
        base_tour, client_ids, population_size, random_fraction
    )


def generate_sweep_population(
    client_ids: list[int],
    cities_by_id: dict[int, City],
    population_size: int,
    random_fraction: float = 0.3,
) -> list[list[int]]:
    """Gera uma população inicial semeada pela heurística da varredura (sweep).

    Args:
        client_ids: IDs dos clientes (sem o depósito 0).
        cities_by_id: Dicionário ID -> City.
        population_size: Quantidade de indivíduos na população.
        random_fraction: Fração da população gerada aleatoriamente (0.0 a 1.0).

    Returns:
        Lista de cromossomos (cada um é uma permutação de client_ids).
    """
    base_tour = sweep_tour(cities_by_id, client_ids)
    return seed_population_from_tour(
        base_tour, client_ids, population_size, random_fraction
    )


def generate_clarke_wright_population(
    client_ids: list[int],
    cities_by_id: dict[int, City],
    fleet: FleetConfig,
    population_size: int,
    random_fraction: float = 0.3,
) -> list[list[int]]:
    """Gera uma população inicial semeada pela heurística das economias (Clarke-Wright).

    Args:
        client_ids: IDs dos clientes (sem o depósito 0).
        cities_by_id: Dicionário ID -> City.
        fleet: Configuração da frota (capacidade usada nas mesclagens).
        population_size: Quantidade de indivíduos na população.
        random_fraction: Fração da população gerada aleatoriamente (0.0 a 1.0).

    Returns:
        Lista de cromossomos (cada um é uma permutação de client_ids).
    """
    base_tour = clarke_wright_tour(cities_by_id, client_ids, fleet)
    return seed_population_from_tour(
        base_tour, client_ids, population_size, random_fraction
    )


def order_crossover(parent1: list[int], parent2: list[int]) -> list[int]:
    """Realiza o crossover por ordem (OX) entre dois pais.

    Args:
        parent1: Primeiro cromossomo pai (lista de IDs).
        parent2: Segundo cromossomo pai (lista de IDs).

    Returns:
        O cromossomo filho resultante.

    Raises:
        ValueError: Se os pais tiverem comprimentos diferentes.
    """
    length = len(parent1)
    if length != len(parent2):
        raise ValueError(
            f"Os pais devem ter o mesmo comprimento: {len(parent1)} != {len(parent2)}"
        )

    child = [-1] * length

    # Seleciona dois pontos de corte aleatórios
    start_index = random.randint(0, length - 1)
    end_index = random.randint(start_index + 1, length)

    # Copia o segmento do pai 1
    child[start_index:end_index] = parent1[start_index:end_index]

    # Preenche o restante com elementos do pai 2, sem duplicar
    child_set = set(parent1[start_index:end_index])
    parent2_idx = 0

    for i in range(length):
        if child[i] == -1:
            while parent2[parent2_idx] in child_set:
                parent2_idx += 1
            child[i] = parent2[parent2_idx]
            parent2_idx += 1

    return child


def pmx_crossover(parent1: list[int], parent2: list[int]) -> list[int]:
    """Realiza o Partially Mapped Crossover (PMX) entre dois pais.

    Copia um segmento do pai 1 e resolve os conflitos do pai 2 via mapeamento
    posicional, preservando posições absolutas sempre que possível.

    Args:
        parent1: Primeiro cromossomo pai (lista de IDs).
        parent2: Segundo cromossomo pai (lista de IDs).

    Returns:
        O cromossomo filho resultante.

    Raises:
        ValueError: Se os pais tiverem comprimentos diferentes.
    """
    length = len(parent1)
    if length != len(parent2):
        raise ValueError(
            f"Os pais devem ter o mesmo comprimento: {len(parent1)} != {len(parent2)}"
        )
    if length < 2:
        return list(parent1)

    start, end = sorted(random.sample(range(length), 2))
    child = [-1] * length
    child[start : end + 1] = parent1[start : end + 1]
    segment = set(parent1[start : end + 1])

    # Resolve os elementos do segmento do pai 2 que ainda não estão no filho
    for i in range(start, end + 1):
        gene = parent2[i]
        if gene in segment:
            continue
        pos = i
        while child[pos] != -1:
            pos = parent2.index(parent1[pos])
        child[pos] = gene

    # Preenche o restante diretamente do pai 2
    for i in range(length):
        if child[i] == -1:
            child[i] = parent2[i]

    return child


def cx_crossover(parent1: list[int], parent2: list[int]) -> list[int]:
    """Realiza o Cycle Crossover (CX) entre dois pais.

    Identifica o ciclo que começa na primeira posição (herdado do pai 1) e
    completa as demais posições com o pai 2, preservando a posição absoluta de
    cada cliente em relação a um dos pais.

    Args:
        parent1: Primeiro cromossomo pai (lista de IDs).
        parent2: Segundo cromossomo pai (lista de IDs).

    Returns:
        O cromossomo filho resultante.

    Raises:
        ValueError: Se os pais tiverem comprimentos diferentes.
    """
    length = len(parent1)
    if length != len(parent2):
        raise ValueError(
            f"Os pais devem ter o mesmo comprimento: {len(parent1)} != {len(parent2)}"
        )
    if length < 2:
        return list(parent1)

    child = [-1] * length

    # Percorre o ciclo iniciado na posição 0, herdando do pai 1
    index = 0
    while child[index] == -1:
        child[index] = parent1[index]
        index = parent1.index(parent2[index])

    # Preenche as posições restantes com o pai 2
    for i in range(length):
        if child[i] == -1:
            child[i] = parent2[i]

    return child


def crossover(parent1: list[int], parent2: list[int], method: str = "ox") -> list[int]:
    """Aplica o operador de crossover escolhido entre dois pais.

    Args:
        parent1: Primeiro cromossomo pai.
        parent2: Segundo cromossomo pai.
        method: "ox" (Order), "pmx" (Partially Mapped) ou "cx" (Cycle).

    Returns:
        O cromossomo filho resultante.

    Raises:
        ValueError: Se o método informado for desconhecido.
    """
    if method == "ox":
        return order_crossover(parent1, parent2)
    if method == "pmx":
        return pmx_crossover(parent1, parent2)
    if method == "cx":
        return cx_crossover(parent1, parent2)
    raise ValueError(f"Método de crossover desconhecido: {method!r}")


def two_opt_step(
    chromosome: list[int],
    cities_by_id: dict[int, City],
) -> list[int]:
    """Aplica um passo de busca local 2-opt guloso ao cromossomo.

    Avalia o tour plano (depósito -> clientes na ordem -> depósito) e encontra a
    reversão de subsegmento que mais reduz a distância total, aplicando-a. Se
    nenhuma reversão melhora, retorna uma cópia inalterada. Diferente da
    `inversion` (reversão aleatória), aqui a reversão é escolhida por melhoria.

    Args:
        chromosome: Lista de IDs de clientes.
        cities_by_id: Dicionário ID -> City (deve conter o depósito 0).

    Returns:
        Cromossomo após o melhor movimento 2-opt (ou cópia, se nada melhora).
    """
    n = len(chromosome)
    if n < 2:
        return list(chromosome)

    depot = (cities_by_id[0].x, cities_by_id[0].y)
    points: list[tuple[float, float]] = [depot]
    points.extend((cities_by_id[cid].x, cities_by_id[cid].y) for cid in chromosome)
    points.append(depot)

    best_delta = -1e-9
    best_move: Optional[tuple[int, int]] = None

    for i in range(1, n + 1):
        a_prev = points[i - 1]
        a = points[i]
        for j in range(i, n + 1):
            b = points[j]
            b_next = points[j + 1]
            delta = (
                calculate_distance(a_prev, b)
                + calculate_distance(a, b_next)
                - calculate_distance(a_prev, a)
                - calculate_distance(b, b_next)
            )
            if delta < best_delta:
                best_delta = delta
                best_move = (i, j)

    if best_move is None:
        return list(chromosome)

    i, j = best_move
    result = list(chromosome)
    result[i - 1 : j] = result[i - 1 : j][::-1]
    return result


def mutate(
    chromosome: list[int],
    mutation_probability: float,
    operator: str = "random",
    cities_by_id: Optional[dict[int, City]] = None,
) -> list[int]:
    """Aplica mutação sob probabilidade, usando o operador escolhido.

    Operadores disponíveis:
    - "swap": troca a posição de dois IDs.
    - "inversion": inverte um subsegmento (reversão aleatória).
    - "reallocate": retira um ID e o reinsere em outra posição.
    - "or_opt": move uma cadeia de 2-3 clientes consecutivos para outra posição.
    - "scramble": embaralha aleatoriamente um subsegmento.
    - "two_opt": reversão GULOSA que mais reduz a distância (busca local; requer
      cities_by_id).
    - "random": sorteia um dos operadores acima a cada chamada.

    Todos preservam a permutação (nenhum cliente é duplicado ou omitido).

    Args:
        chromosome: Lista de IDs do cromossomo.
        mutation_probability: Chance de ocorrer mutação (0.0 a 1.0).
        operator: Operador a aplicar (ver lista acima).
        cities_by_id: Dicionário ID -> City; obrigatório para "two_opt".

    Returns:
        Nova lista de IDs do cromossomo (possivelmente mutado).

    Raises:
        ValueError: Se o operador informado for desconhecido.
    """
    if len(chromosome) < 2 or random.random() >= mutation_probability:
        return list(chromosome)

    if operator == "random":
        pool = ["swap", "inversion", "reallocate", "or_opt", "scramble"]
        if cities_by_id is not None:
            pool.append("two_opt")
        operator = random.choice(pool)

    mutated = list(chromosome)

    if operator == "swap":
        idx1, idx2 = random.sample(range(len(mutated)), 2)
        mutated[idx1], mutated[idx2] = mutated[idx2], mutated[idx1]

    elif operator == "inversion":
        idx1 = random.randint(0, len(mutated) - 2)
        idx2 = random.randint(idx1 + 2, len(mutated))
        mutated[idx1:idx2] = mutated[idx1:idx2][::-1]

    elif operator == "reallocate":
        idx_from = random.randrange(len(mutated))
        city = mutated.pop(idx_from)
        idx_to = random.randrange(len(mutated) + 1)
        mutated.insert(idx_to, city)

    elif operator == "or_opt":
        max_seg = min(3, len(mutated) - 1)
        seg_len = random.randint(min(2, max_seg), max_seg)
        start = random.randint(0, len(mutated) - seg_len)
        segment = mutated[start : start + seg_len]
        del mutated[start : start + seg_len]
        insert_pos = random.randint(0, len(mutated))
        mutated[insert_pos:insert_pos] = segment

    elif operator == "scramble":
        idx1 = random.randint(0, len(mutated) - 2)
        idx2 = random.randint(idx1 + 2, len(mutated))
        segment = mutated[idx1:idx2]
        random.shuffle(segment)
        mutated[idx1:idx2] = segment

    elif operator == "two_opt":
        if cities_by_id is None:
            # Sem coordenadas não há como avaliar distância: cai na inversão.
            idx1 = random.randint(0, len(mutated) - 2)
            idx2 = random.randint(idx1 + 2, len(mutated))
            mutated[idx1:idx2] = mutated[idx1:idx2][::-1]
        else:
            mutated = two_opt_step(mutated, cities_by_id)

    else:
        raise ValueError(f"Operador de mutação desconhecido: {operator!r}")

    return mutated


def sort_population(
    population: list[list[int]],
    fitness: list[float],
) -> tuple[list[list[int]], list[float]]:
    """Ordena a população e seus respectivos valores de fitness (menor para maior).

    Args:
        population: Lista de cromossomos.
        fitness: Lista de pontuações correspondentes.

    Returns:
        Tupla contendo (população_ordenada, fitness_ordenado).
    """
    combined = list(zip(population, fitness))
    sorted_combined = sorted(combined, key=lambda x: x[1])
    sorted_pop, sorted_fit = zip(*sorted_combined)
    return list(sorted_pop), list(sorted_fit)


def _tournament_select(
    population: list[list[int]],
    fitness: list[float],
    tournament_size: int,
) -> list[int]:
    """Seleciona um indivíduo por torneio: sorteia k concorrentes e vence o melhor.

    Args:
        population: Lista de cromossomos.
        fitness: Lista de pontuações correspondentes (menor é melhor).
        tournament_size: Número de concorrentes no torneio.

    Returns:
        O cromossomo vencedor (menor fitness entre os sorteados).
    """
    size = max(1, min(tournament_size, len(population)))
    contenders = random.sample(range(len(population)), size)
    winner = min(contenders, key=lambda i: fitness[i])
    return population[winner]


def select_parents(
    population: list[list[int]],
    fitness: list[float],
    method: str = "rank",
    tournament_size: int = 3,
) -> tuple[list[int], list[int]]:
    """Seleciona dois pais da população usando o método escolhido.

    Métodos disponíveis (sempre tratando MENOR fitness como melhor):
    - "rank": probabilidade proporcional à posição no ranking de fitness.
    - "tournament": dois torneios independentes de `tournament_size` concorrentes.
    - "roulette": probabilidade proporcional a 1/fitness (evita o overflow que a
      roleta clássica teria com as penalidades grandes do fitness).

    Args:
        population: Lista de cromossomos.
        fitness: Lista de pontuações correspondentes.
        method: "rank", "tournament" ou "roulette".
        tournament_size: Tamanho do torneio (usado apenas em "tournament").

    Returns:
        Tupla com dois cromossomos pais.

    Raises:
        ValueError: Se o método informado for desconhecido.
    """
    n = len(population)

    if method == "rank":
        order = sorted(range(n), key=lambda i: fitness[i])
        weights = [0.0] * n
        for rank, idx in enumerate(order):
            weights[idx] = float(n - rank)
        parent1, parent2 = random.choices(population, weights=weights, k=2)
        return parent1, parent2

    if method == "roulette":
        weights = [
            1.0 / f if (f != float("inf") and f > 0) else 0.0 for f in fitness
        ]
        if sum(weights) <= 0:
            weights = [1.0] * n
        parent1, parent2 = random.choices(population, weights=weights, k=2)
        return parent1, parent2

    if method == "tournament":
        return (
            _tournament_select(population, fitness, tournament_size),
            _tournament_select(population, fitness, tournament_size),
        )

    raise ValueError(f"Método de seleção desconhecido: {method!r}")
