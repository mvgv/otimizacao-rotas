# -*- coding: utf-8 -*-
"""Testes de unidade e fuzzing para as operações do Algoritmo Genético do VRP."""

# 1. Biblioteca padrão
import random

# 2. Bibliotecas de terceiros

# 3. Módulos locais
from genetic_algorithm import (
    City,
    FleetConfig,
    create_cities_from_locations,
    split_routes,
    calculate_fitness,
    order_crossover,
    mutate,
    sort_population,
)


def test_create_cities_from_locations() -> None:
    """Verifica se create_cities_from_locations cria objetos City válidos."""
    locations = [(100, 100), (200, 200), (300, 300)]
    cities = create_cities_from_locations(locations)

    assert len(cities) == 3
    assert cities[0].id == 0
    assert cities[0].x == 100
    assert cities[0].y == 100
    assert cities[0].demand == 0.0
    assert cities[0].priority == 0

    assert cities[1].id == 1
    assert cities[1].demand > 0.0
    assert cities[2].id == 2


def test_split_routes_capacity() -> None:
    """Verifica se split_routes divide as rotas de acordo com a capacidade do veículo."""
    cities_by_id = {
        0: City(id=0, x=0, y=0, demand=0.0, priority=0),
        1: City(id=1, x=10, y=0, demand=40.0, priority=1),
        2: City(id=2, x=20, y=0, demand=40.0, priority=1),
        3: City(id=3, x=30, y=0, demand=30.0, priority=1),
    }
    fleet = FleetConfig(num_vehicles=3, vehicle_capacity=50.0, vehicle_autonomy=1000.0)

    # Cromossomo: [1, 2, 3].
    # Veículo 1 pega 1 (load=40). 2 excede (40+40=80 > 50). split_routes abre veículo 2.
    # Veículo 2 pega 2 (load=40). 3 excede (40+30=70 > 50). split_routes abre veículo 3.
    # Veículo 3 pega 3.
    routes = split_routes([1, 2, 3], cities_by_id, fleet)
    assert routes == [[1], [2], [3]]

    # Com capacidade 90:
    # Veículo 1 pega 1 e 2 (load=80). 3 excede (80+30=110 > 90). split_routes abre veículo 2.
    # Veículo 2 pega 3.
    fleet_large = FleetConfig(
        num_vehicles=3, vehicle_capacity=90.0, vehicle_autonomy=1000.0
    )
    routes_large = split_routes([1, 2, 3], cities_by_id, fleet_large)
    assert routes_large == [[1, 2], [3]]


def test_split_routes_autonomy() -> None:
    """Verifica se split_routes divide as rotas de acordo com a autonomia de distância."""
    # Depot em (0, 0)
    # Cidades distantes: dist(depot, 1)=100, dist(1, 2)=10, dist(2, depot)=110
    cities_by_id = {
        0: City(id=0, x=0, y=0, demand=0.0, priority=0),
        1: City(id=1, x=100, y=0, demand=10.0, priority=1),
        2: City(id=2, x=110, y=0, demand=10.0, priority=1),
    }
    # Se autonomia for 210, cabe ir para 1 e voltar para o depósito (200),
    # mas ir para 1 e depois para 2 e voltar ao depósito exige 100 + 10 + 110 = 220.
    fleet = FleetConfig(num_vehicles=2, vehicle_capacity=100.0, vehicle_autonomy=210.0)
    routes = split_routes([1, 2], cities_by_id, fleet)
    assert routes == [[1], [2]]


def test_calculate_fitness() -> None:
    """Verifica se calculate_fitness calcula a distância mais penalidades corretamente."""
    cities_by_id = {
        0: City(id=0, x=0, y=0, demand=0.0, priority=0),
        1: City(id=1, x=100, y=0, demand=10.0, priority=1),
        2: City(id=2, x=200, y=0, demand=10.0, priority=1),
    }
    fleet = FleetConfig(num_vehicles=1, vehicle_capacity=5.0, vehicle_autonomy=50.0)

    # 1 veículo disponível, capacidade 5, autonomia 50.
    # A rota [1, 2] vai precisar de 2 veículos (cargas 10 > 5).
    # Como a frota disponível é 1, teremos penalidade de quantidade de veículos (1 extra = +5000)
    # E possivelmente de autonomia ou de capacidade se algum veículo individual violar.
    # Aqui, a rota gerará 2 sub-rotas: [[1], [2]]
    # Sub-rota 1: load=10 > 5 -> penalidade capacidade = (10-5)*1000 = 5000. dist = 100+100 = 200 > 50 -> penalidade autonomia = 150000.
    # Total de veículos é 2 > 1 -> penalidade frota = 5000.
    fitness = calculate_fitness([1, 2], cities_by_id, fleet)
    assert fitness > 5000.0


def test_order_crossover_preserves_all_clients() -> None:
    """Verifica se o cruzamento OX preserva todos os clientes exatamente uma vez."""
    parent1 = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    parent2 = [9, 8, 7, 6, 5, 4, 3, 2, 1]

    child = order_crossover(parent1, parent2)
    assert len(child) == 9
    assert sorted(child) == [1, 2, 3, 4, 5, 6, 7, 8, 9]


def test_order_crossover_fuzz() -> None:
    """Fuzz testing de order_crossover com 1000 iterações aleatórias."""
    length = 20
    parent1 = list(range(1, length + 1))
    parent2 = list(range(1, length + 1))

    for _ in range(1000):
        random.shuffle(parent1)
        random.shuffle(parent2)
        child = order_crossover(parent1, parent2)
        assert len(child) == length
        assert sorted(child) == list(range(1, length + 1))


def test_mutate_fuzz() -> None:
    """Fuzz testing de mutate garantindo que a estrutura do cromossomo nunca seja corrompida."""
    length = 15
    original = list(range(1, length + 1))

    for _ in range(1000):
        mutated = mutate(original, 1.0)
        assert len(mutated) == length
        assert sorted(mutated) == list(range(1, length + 1))


def test_sort_population() -> None:
    """Verifica se a ordenação da população funciona como esperado."""
    population = [[1, 2], [2, 1], [1, 1]]
    fitness = [15.5, 5.2, 22.0]
    sorted_pop, sorted_fit = sort_population(population, fitness)

    assert sorted_fit == [5.2, 15.5, 22.0]
    assert sorted_pop[0] == [2, 1]
    assert sorted_pop[1] == [1, 2]
    assert sorted_pop[2] == [1, 1]
