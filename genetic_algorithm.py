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
from typing import Optional

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


def mutate(chromosome: list[int], mutation_probability: float) -> list[int]:
    """Aplica mutação sob probabilidade, escolhendo entre três operadores.

    Os operadores são:
    1. Swap: Troca a posição de dois IDs.
    2. Inversion: Inverte um subsegmento do cromossomo.
    3. Reallocate: Retira um ID de um ponto e o insere em outro.

    Args:
        chromosome: Lista de IDs do cromossomo.
        mutation_probability: Chance de ocorrer mutação (0.0 a 1.0).

    Returns:
        Nova lista de IDs do cromossomo mutado.
    """
    if len(chromosome) < 2 or random.random() >= mutation_probability:
        return list(chromosome)

    mutated = list(chromosome)
    mutation_type = random.choice(["swap", "inversion", "reallocate"])

    if mutation_type == "swap":
        idx1, idx2 = random.sample(range(len(mutated)), 2)
        mutated[idx1], mutated[idx2] = mutated[idx2], mutated[idx1]

    elif mutation_type == "inversion":
        idx1 = random.randint(0, len(mutated) - 2)
        idx2 = random.randint(idx1 + 2, len(mutated))
        mutated[idx1:idx2] = list(reversed(mutated[idx1:idx2]))

    elif mutation_type == "reallocate":
        idx_from = random.randrange(len(mutated))
        city = mutated.pop(idx_from)
        idx_to = random.randrange(len(mutated) + 1)
        mutated.insert(idx_to, city)

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
