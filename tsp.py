# -*- coding: utf-8 -*-
"""Módulo principal que executa o solucionador de Roteamento de Veículos (VRP) com AG.

Este script inicializa a interface gráfica do Pygame, cria a população inicial,
executa o loop evolutivo exibindo os caminhos e as métricas na tela em tempo real.
"""

# 1. Biblioteca padrão
import itertools
import random
import sys

# 2. Bibliotecas de terceiros
import pygame
from pygame.locals import QUIT, KEYDOWN, K_q

# 3. Módulos locais
from draw_functions import draw_cities, draw_paths, draw_plot, draw_stats_panel
from genetic_algorithm import (
    FleetConfig,
    create_cities_from_locations,
    generate_random_population,
    calculate_fitness,
    split_routes,
    sort_population,
    order_crossover,
    mutate,
)

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
MUTATION_PROBABILITY = 0.4

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

# Inicialização das Cidades (Hospital na primeira posição)
# O Hospital (ID 0) fica fixo no centro do mapa
depot_x = PLOT_X_OFFSET + MAP_WIDTH // 2
depot_y = HEIGHT // 2
cities_locations = [(depot_x, depot_y)]

# Adiciona as outras cidades aleatoriamente na área do mapa
for _ in range(N_CITIES - 1):
    cities_locations.append(
        (
            random.randint(PLOT_X_OFFSET + 30, PLOT_X_OFFSET + MAP_WIDTH - 30),
            random.randint(30, HEIGHT - 30),
        )
    )

# --- Opção: Usar um problema padrão (Descomente para usar) ---
# cities_locations = default_problems[15]
# N_CITIES = len(cities_locations)
# -------------------------------------------------------------

# --- Opção: Usar o benchmark att48 (Descomente para usar) ---
# scale_x = (MAP_WIDTH - 60) / max(p[0] for p in att_48_cities_locations)
# scale_y = (HEIGHT - 60) / max(p[1] for p in att_48_cities_locations)
# cities_locations = [
#     (
#         int(p[0] * scale_x + PLOT_X_OFFSET + 30),
#         int(p[1] * scale_y + 30)
#     ) for p in att_48_cities_locations
# ]
# N_CITIES = len(cities_locations)
# -------------------------------------------------------------

cities_by_id = create_cities_from_locations(cities_locations)
cities_ids = list(range(1, N_CITIES))

# Inicialização do Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Otimizador de Rotas de Entrega Hospitalar (VRP)")
clock = pygame.time.Clock()
generation_counter = itertools.count(start=1)

# Cria a população inicial (permutação de IDs de cidades de 1 a N-1)
population = generate_random_population(cities_ids, POPULATION_SIZE)
best_fitness_values: list[float] = []
best_solutions: list[list[int]] = []

running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == KEYDOWN:
            if event.key == K_q:
                running = False

    generation = next(generation_counter)
    screen.fill((248, 249, 250))  # Cor de fundo clara para contraste

    # Avaliação da População
    population_fitness = [
        calculate_fitness(individual, cities_by_id, fleet) for individual in population
    ]

    # Ordenação da população por aptidão
    population, population_fitness = sort_population(population, population_fitness)

    best_fitness = population_fitness[0]
    best_solution = population[0]

    best_fitness_values.append(best_fitness)
    best_solutions.append(best_solution)

    # Desenha o gráfico de convergência na metade esquerda
    draw_plot(screen, list(range(1, len(best_fitness_values) + 1)), best_fitness_values)

    # Desenha as cidades no mapa
    draw_cities(screen, cities_by_id, NODE_RADIUS)

    # Divide o melhor cromossomo em rotas e desenha
    best_routes = split_routes(best_solution, cities_by_id, fleet)
    draw_paths(screen, best_routes, cities_by_id, VEHICLE_COLORS)

    # Desenha o painel de informações da frota no canto direito
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

    print(
        f"Geração {generation}: Melhor Custo = {round(best_fitness, 2)} (Rotas: {len(best_routes)})"
    )

    # Geração da nova população
    new_population = [population[0]]  # Elitismo: preserva o melhor indivíduo

    # Seleção por Rank (proporcional à posição na lista ordenada)
    # Garante seleção probabilística sem overflow devido a altas penalidades
    selection_weights = [POPULATION_SIZE - i for i in range(POPULATION_SIZE)]

    while len(new_population) < POPULATION_SIZE:
        # SELEÇÃO (Escolhe dois pais com base em seus pesos de rank)
        parent1, parent2 = random.choices(population, weights=selection_weights, k=2)

        # CROSSOVER (Usa dois pais diferentes, corrigindo bug original)
        child1 = order_crossover(parent1, parent2)

        # MUTAÇÃO
        child1 = mutate(child1, MUTATION_PROBABILITY)

        new_population.append(child1)

    population = new_population

    pygame.display.flip()
    clock.tick(FPS)

# Finaliza o Pygame
pygame.quit()
sys.exit()
