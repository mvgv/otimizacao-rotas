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
    convex_hull,
    hull_insertion_tour,
    generate_hull_seeded_population,
    nearest_neighbor_tour,
    sweep_tour,
    clarke_wright_tour,
    generate_nearest_neighbor_population,
    generate_sweep_population,
    generate_clarke_wright_population,
    order_crossover,
    pmx_crossover,
    cx_crossover,
    crossover,
    select_parents,
    mutate,
    two_opt_step,
    calculate_distance,
    sort_population,
)


def _flat_tour_distance(
    chromosome: list[int], cities_by_id: dict[int, City]
) -> float:
    """Distância do tour plano: depósito -> clientes na ordem -> depósito."""
    depot = cities_by_id[0]
    points = (
        [(depot.x, depot.y)]
        + [(cities_by_id[c].x, cities_by_id[c].y) for c in chromosome]
        + [(depot.x, depot.y)]
    )
    return sum(
        calculate_distance(points[k], points[k + 1]) for k in range(len(points) - 1)
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


def test_convex_hull_square() -> None:
    """Verifica se o convex hull retorna só os vértices, ignorando pontos internos."""
    # Quatro cantos de um quadrado + um ponto central interno (índice 4)
    points = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (5.0, 5.0)]
    hull = convex_hull(points)

    assert set(hull) == {0, 1, 2, 3}
    assert 4 not in hull


def test_convex_hull_few_points() -> None:
    """Verifica o caso degenerado de menos de 3 pontos."""
    assert convex_hull([(0.0, 0.0), (1.0, 1.0)]) == [0, 1]


def test_hull_insertion_tour_preserves_clients() -> None:
    """Verifica se a rota-base do hull contém todos os clientes exatamente uma vez."""
    locations = [(50, 50)] + [(i * 10, (i * 7) % 50) for i in range(1, 13)]
    cities_by_id = create_cities_from_locations(locations)
    client_ids = list(range(1, len(locations)))

    tour = hull_insertion_tour(cities_by_id, client_ids)

    assert len(tour) == len(client_ids)
    assert sorted(tour) == sorted(client_ids)


def test_generate_hull_seeded_population() -> None:
    """Verifica tamanho e validade dos cromossomos da população semeada pelo hull."""
    locations = [(50, 50)] + [(i * 11, (i * 13) % 60) for i in range(1, 16)]
    cities_by_id = create_cities_from_locations(locations)
    client_ids = list(range(1, len(locations)))
    population_size = 100

    population = generate_hull_seeded_population(
        client_ids, cities_by_id, population_size
    )

    assert len(population) == population_size
    for individual in population:
        assert sorted(individual) == sorted(client_ids)


def test_nearest_neighbor_tour() -> None:
    """Verifica se o vizinho mais próximo preserva clientes e segue o mais próximo."""
    # Depósito em (0,0); clientes em linha. Partindo do depósito, a ordem natural
    # mais próxima é 1 -> 2 -> 3.
    cities_by_id = {
        0: City(id=0, x=0, y=0, demand=0.0, priority=0),
        1: City(id=1, x=10, y=0, demand=5.0, priority=1),
        2: City(id=2, x=20, y=0, demand=5.0, priority=1),
        3: City(id=3, x=30, y=0, demand=5.0, priority=1),
    }
    tour = nearest_neighbor_tour(cities_by_id, [1, 2, 3])
    assert tour == [1, 2, 3]
    assert sorted(tour) == [1, 2, 3]


def test_sweep_tour_preserves_clients() -> None:
    """Verifica se a varredura ordena por ângulo e mantém todos os clientes."""
    # Depósito no centro; clientes em quadrantes distintos.
    cities_by_id = {
        0: City(id=0, x=0, y=0, demand=0.0, priority=0),
        1: City(id=1, x=10, y=1, demand=5.0, priority=1),  # ~0 rad
        2: City(id=2, x=0, y=10, demand=5.0, priority=1),  # ~pi/2
        3: City(id=3, x=-10, y=1, demand=5.0, priority=1),  # ~pi
    }
    tour = sweep_tour(cities_by_id, [3, 1, 2])
    assert tour == [1, 2, 3]
    assert sorted(tour) == [1, 2, 3]


def test_clarke_wright_tour_preserves_clients() -> None:
    """Verifica se o Clarke-Wright preserva todos os clientes exatamente uma vez."""
    locations = [(50, 50)] + [(i * 9, (i * 17) % 70) for i in range(1, 14)]
    cities_by_id = create_cities_from_locations(locations)
    client_ids = list(range(1, len(locations)))
    fleet = FleetConfig(num_vehicles=4, vehicle_capacity=80.0, vehicle_autonomy=2000.0)

    tour = clarke_wright_tour(cities_by_id, client_ids, fleet)
    assert len(tour) == len(client_ids)
    assert sorted(tour) == sorted(client_ids)


def test_seeded_populations_are_valid() -> None:
    """Verifica tamanho e validade das populações semeadas por NN, sweep e savings."""
    locations = [(50, 50)] + [(i * 11, (i * 13) % 60) for i in range(1, 16)]
    cities_by_id = create_cities_from_locations(locations)
    client_ids = list(range(1, len(locations)))
    fleet = FleetConfig(num_vehicles=4, vehicle_capacity=90.0, vehicle_autonomy=2000.0)
    population_size = 100

    populations = [
        generate_nearest_neighbor_population(client_ids, cities_by_id, population_size),
        generate_sweep_population(client_ids, cities_by_id, population_size),
        generate_clarke_wright_population(
            client_ids, cities_by_id, fleet, population_size
        ),
    ]

    for population in populations:
        assert len(population) == population_size
        for individual in population:
            assert sorted(individual) == sorted(client_ids)


def test_mutate_operators_preserve_permutation() -> None:
    """Fuzz: todos os operadores de mutação preservam a permutação dos clientes."""
    length = 15
    original = list(range(1, length + 1))
    locations = [(50, 50)] + [
        ((i * 7) % 80, (i * 11) % 60) for i in range(1, length + 1)
    ]
    cities_by_id = create_cities_from_locations(locations)

    operators = [
        "swap",
        "inversion",
        "reallocate",
        "or_opt",
        "scramble",
        "two_opt",
        "random",
    ]
    for op in operators:
        for _ in range(200):
            mutated = mutate(original, 1.0, operator=op, cities_by_id=cities_by_id)
            assert len(mutated) == length
            assert sorted(mutated) == original


def test_mutate_unknown_operator_raises() -> None:
    """Verifica que um operador desconhecido levanta ValueError."""
    import pytest

    with pytest.raises(ValueError):
        # mutation_probability=1.0 garante que a mutação dispara
        mutate([1, 2, 3], 1.0, operator="inexistente")


def test_two_opt_step_never_worsens() -> None:
    """Verifica que o 2-opt guloso nunca piora e preserva todos os clientes."""
    locations = [(0, 0), (10, 0), (0, 10), (10, 10), (5, 20)]
    cities_by_id = create_cities_from_locations(locations)
    client_ids = [1, 2, 3, 4]

    for _ in range(50):
        random.shuffle(client_ids)
        chromosome = list(client_ids)
        improved = two_opt_step(chromosome, cities_by_id)

        assert sorted(improved) == [1, 2, 3, 4]
        assert _flat_tour_distance(improved, cities_by_id) <= _flat_tour_distance(
            chromosome, cities_by_id
        ) + 1e-6


def test_two_opt_step_fixes_crossing() -> None:
    """Verifica que o 2-opt desfaz um cruzamento óbvio, reduzindo a distância."""
    # Quadrado: depósito (0,0); cantos em (10,0),(10,10),(0,10).
    # A ordem [2, 1, 3] cruza; o 2-opt deve encurtar para o perímetro.
    cities_by_id = {
        0: City(id=0, x=0, y=0, demand=0.0, priority=0),
        1: City(id=1, x=10, y=0, demand=5.0, priority=1),
        2: City(id=2, x=10, y=10, demand=5.0, priority=1),
        3: City(id=3, x=0, y=10, demand=5.0, priority=1),
    }
    bad = [2, 1, 3]
    fixed = two_opt_step(bad, cities_by_id)
    assert _flat_tour_distance(fixed, cities_by_id) < _flat_tour_distance(
        bad, cities_by_id
    )


def test_pmx_and_cx_preserve_all_clients() -> None:
    """Verifica que PMX e CX preservam todos os clientes exatamente uma vez."""
    parent1 = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    parent2 = [9, 8, 7, 6, 5, 4, 3, 2, 1]

    for child in (pmx_crossover(parent1, parent2), cx_crossover(parent1, parent2)):
        assert len(child) == 9
        assert sorted(child) == [1, 2, 3, 4, 5, 6, 7, 8, 9]


def test_crossover_fuzz() -> None:
    """Fuzz: todos os operadores de crossover preservam a permutação."""
    length = 20
    parent1 = list(range(1, length + 1))
    parent2 = list(range(1, length + 1))

    for method in ("ox", "pmx", "cx"):
        for _ in range(500):
            random.shuffle(parent1)
            random.shuffle(parent2)
            child = crossover(parent1, parent2, method=method)
            assert len(child) == length
            assert sorted(child) == list(range(1, length + 1))


def test_crossover_unknown_raises() -> None:
    """Verifica que um método de crossover desconhecido levanta ValueError."""
    import pytest

    with pytest.raises(ValueError):
        crossover([1, 2], [2, 1], method="inexistente")


def test_select_parents_returns_members() -> None:
    """Verifica que todos os métodos de seleção retornam indivíduos da população."""
    population = [[1, 2, 3], [3, 2, 1], [2, 1, 3], [1, 3, 2]]
    fitness = [10.0, 5.0, 20.0, 7.0]

    for method in ("rank", "tournament", "roulette"):
        parent1, parent2 = select_parents(population, fitness, method=method)
        assert parent1 in population
        assert parent2 in population


def test_tournament_full_size_returns_best() -> None:
    """Torneio com tamanho = população sempre devolve o de menor fitness."""
    population = [[1, 2, 3], [3, 2, 1], [2, 1, 3]]
    fitness = [10.0, 5.0, 20.0]

    parent1, parent2 = select_parents(
        population, fitness, method="tournament", tournament_size=3
    )
    assert parent1 == [3, 2, 1]
    assert parent2 == [3, 2, 1]


def test_select_parents_unknown_raises() -> None:
    """Verifica que um método de seleção desconhecido levanta ValueError."""
    import pytest

    with pytest.raises(ValueError):
        select_parents([[1, 2]], [1.0], method="inexistente")


def test_sort_population() -> None:
    """Verifica se a ordenação da população funciona como esperado."""
    population = [[1, 2], [2, 1], [1, 1]]
    fitness = [15.5, 5.2, 22.0]
    sorted_pop, sorted_fit = sort_population(population, fitness)

    assert sorted_fit == [5.2, 15.5, 22.0]
    assert sorted_pop[0] == [2, 1]
    assert sorted_pop[1] == [1, 2]
    assert sorted_pop[2] == [1, 1]
