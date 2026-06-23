# -*- coding: utf-8 -*-
"""Módulo de desenho e visualização gráfica utilizando Pygame e Matplotlib."""

# 1. Biblioteca padrão
import math

# 2. Bibliotecas de terceiros
import matplotlib
import matplotlib.pyplot as plt
import pygame
from matplotlib.backends.backend_agg import FigureCanvasAgg

# 3. Módulos locais
from genetic_algorithm import City, FleetConfig, calculate_distance

matplotlib.use("Agg")


def draw_plot(
    screen: pygame.Surface,
    x: list[int],
    y: list[float],
    x_label: str = "Geração",
    y_label: str = "Custo (Distância + Penalidades)",
) -> None:
    """Desenha o gráfico de convergência do fitness na tela do Pygame.

    Args:
        screen: Superfície do Pygame para desenhar.
        x: Valores do eixo X (gerações).
        y: Valores do eixo Y (fitness).
        x_label: Rótulo do eixo X.
        y_label: Rótulo do eixo Y.
    """
    fig, ax = plt.subplots(figsize=(4, 5), dpi=100)
    ax.plot(x, y, color="#1E88E5", linewidth=2)
    ax.set_ylabel(y_label, fontsize=9)
    ax.set_xlabel(x_label, fontsize=9)
    ax.set_title("Convergência do AG", fontsize=10, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    renderer = canvas.get_renderer()
    raw_data = renderer.tostring_rgb()

    size = canvas.get_width_height()
    surf = pygame.image.fromstring(raw_data, size, "RGB")
    screen.blit(surf, (0, 0))
    plt.close(fig)


def draw_cities(
    screen: pygame.Surface,
    cities_by_id: dict[int, City],
    node_radius: int = 8,
) -> None:
    """Desenha as cidades na tela, distinguindo o hospital e as prioridades.

    - Hospital (ID 0): Quadrado vermelho com borda preta.
    - Medicamento Crítico (Prioridade 10): Círculo vermelho pulsante/duplo.
    - Insumo Regular (Prioridade 1): Círculo azul.

    Args:
        screen: Superfície do Pygame.
        cities_by_id: Dicionário ID -> City.
        node_radius: Raio dos círculos para as cidades normais.
    """
    # Cores
    color_depot = (220, 53, 69)  # Vermelho escuro/brilhante
    color_critical = (253, 126, 20)  # Laranja/Vermelho
    color_regular = (13, 110, 253)  # Azul
    color_border = (33, 37, 41)  # Cinza escuro/preto

    # Desenha o Hospital primeiro para que as linhas fiquem atrás
    depot = cities_by_id[0]
    depot_rect = pygame.Rect(depot.x - 10, depot.y - 10, 20, 20)
    pygame.draw.rect(screen, color_depot, depot_rect)
    pygame.draw.rect(screen, color_border, depot_rect, width=2)

    # Desenha uma cruz branca no hospital (ícone de hospital)
    pygame.draw.line(
        screen, (255, 255, 255), (depot.x, depot.y - 6), (depot.x, depot.y + 6), 3
    )
    pygame.draw.line(
        screen, (255, 255, 255), (depot.x - 6, depot.y), (depot.x + 6, depot.y), 3
    )

    # Desenha as outras cidades
    for city_id, city in cities_by_id.items():
        if city_id == 0:
            continue

        if city.priority >= 10:
            # Medicamento Crítico: desenha com círculo duplo
            pygame.draw.circle(
                screen, color_critical, (city.x, city.y), node_radius + 2
            )
            pygame.draw.circle(
                screen, (255, 255, 255), (city.x, city.y), node_radius - 1
            )
            pygame.draw.circle(
                screen, color_critical, (city.x, city.y), node_radius - 3
            )
            pygame.draw.circle(
                screen, color_border, (city.x, city.y), node_radius + 2, width=1
            )
        else:
            # Insumo Regular
            pygame.draw.circle(screen, color_regular, (city.x, city.y), node_radius)
            pygame.draw.circle(
                screen, color_border, (city.x, city.y), node_radius, width=1
            )

        # Desenha o ID da cidade acima dela para facilitar interpretação
        pygame.font.init()
        font = pygame.font.SysFont("Arial", 11, bold=True)
        text_surf = font.render(str(city.id), True, color_border)
        screen.blit(text_surf, (city.x - 5, city.y - 20))


def draw_paths(
    screen: pygame.Surface,
    routes: list[list[int]],
    cities_by_id: dict[int, City],
    colors: list[tuple[int, int, int]],
    width: int = 3,
) -> None:
    """Desenha os caminhos de cada veículo com cores distintas.

    Args:
        screen: Superfície do Pygame.
        routes: Lista de rotas por veículo.
        cities_by_id: Dicionário ID -> City.
        colors: Lista de cores RGB.
        width: Largura das linhas de caminho.
    """
    depot = cities_by_id[0]

    for i, route in enumerate(routes):
        if not route:
            continue

        color = colors[i % len(colors)]

        # Constrói o caminho completo iniciando e retornando ao depósito
        points = [(depot.x, depot.y)]
        for city_id in route:
            city = cities_by_id[city_id]
            points.append((city.x, city.y))
        points.append((depot.x, depot.y))

        # Desenha as linhas da rota
        pygame.draw.lines(screen, color, False, points, width=width)

        # Desenha setas de direção em cada trecho para orientar o fluxo da entrega
        for j in range(len(points) - 1):
            p1 = points[j]
            p2 = points[j + 1]

            # Ponto médio do segmento
            mid_x = (p1[0] + p2[0]) / 2
            mid_y = (p1[1] + p2[1]) / 2

            # Vetor direção
            dx = float(p2[0] - p1[0])
            dy = float(p2[1] - p1[1])
            length = math.sqrt(dx**2 + dy**2)

            if length > 0:
                dx /= length
                dy /= length

                # Pontos da ponta da seta
                arrow_length = 8
                arrow_width = 5

                # Vetor perpendicular
                px = -dy
                py = dx

                pt_arrow_base = (mid_x - arrow_length * dx, mid_y - arrow_length * dy)
                pt_left = (
                    pt_arrow_base[0] + arrow_width * px,
                    pt_arrow_base[1] + arrow_width * py,
                )
                pt_right = (
                    pt_arrow_base[0] - arrow_width * px,
                    pt_arrow_base[1] - arrow_width * py,
                )

                pygame.draw.polygon(screen, color, [(mid_x, mid_y), pt_left, pt_right])


def draw_stats_panel(
    screen: pygame.Surface,
    routes: list[list[int]],
    cities_by_id: dict[int, City],
    fleet: FleetConfig,
    colors: list[tuple[int, int, int]],
    panel_x: int,
    panel_y: int,
    panel_width: int,
    panel_height: int,
) -> None:
    """Desenha um painel informativo detalhado sobre a frota no canto direito da tela.

    Args:
        screen: Superfície do Pygame.
        routes: Lista de rotas por veículo.
        cities_by_id: Dicionário ID -> City.
        fleet: Configuração da frota.
        colors: Cores de cada veículo correspondente.
        panel_x: Coordenada X inicial do painel.
        panel_y: Coordenada Y inicial do painel.
        panel_width: Largura do painel.
        panel_height: Altura do painel.
    """
    pygame.font.init()
    title_font = pygame.font.SysFont("Arial", 14, bold=True)
    body_font = pygame.font.SysFont("Arial", 11)
    status_font = pygame.font.SysFont("Arial", 10, bold=True)

    # Cor de fundo do painel (cinza escuro premium com borda)
    pygame.draw.rect(
        screen, (30, 33, 36), (panel_x, panel_y, panel_width, panel_height)
    )
    pygame.draw.rect(
        screen, (79, 84, 92), (panel_x, panel_y, panel_width, panel_height), width=2
    )

    # Título do Painel
    title_surf = title_font.render("DASHBOARD DA FROTA", True, (255, 255, 255))
    screen.blit(title_surf, (panel_x + 15, panel_y + 15))
    pygame.draw.line(
        screen,
        (79, 84, 92),
        (panel_x + 15, panel_y + 35),
        (panel_x + panel_width - 15, panel_y + 35),
        2,
    )

    # Informações globais
    global_y = panel_y + 45
    txt_vehicles = f"Veículos Ativos: {len(routes)} / {fleet.num_vehicles}"
    screen.blit(
        body_font.render(txt_vehicles, True, (200, 200, 200)), (panel_x + 15, global_y)
    )

    # Verifica se há infração global de quantidade de veículos
    if len(routes) > fleet.num_vehicles:
        alert_surf = status_font.render("EXCESSO DE VEÍCULOS!", True, (255, 50, 50))
        screen.blit(alert_surf, (panel_x + 15, global_y + 15))
        global_y += 30
    else:
        global_y += 15

    # Separador para os veículos
    pygame.draw.line(
        screen,
        (79, 84, 92),
        (panel_x + 15, global_y + 10),
        (panel_x + panel_width - 15, global_y + 10),
        1,
    )

    vehicle_y = global_y + 20
    depot = cities_by_id[0]

    for i in range(max(len(routes), fleet.num_vehicles)):
        # Desenha a seção para cada veículo
        color = colors[i % len(colors)]

        # Quadrado colorido do veículo
        pygame.draw.rect(screen, color, (panel_x + 15, vehicle_y, 12, 12))

        vehicle_title = f"Veículo {i + 1}"
        screen.blit(
            title_font.render(vehicle_title, True, (255, 255, 255)),
            (panel_x + 35, vehicle_y - 2),
        )

        if i < len(routes):
            route = routes[i]
            # Calcula carga útil e distância para esta rota
            load = 0.0
            dist = 0.0
            last_city = depot
            for city_id in route:
                city = cities_by_id[city_id]
                dist += calculate_distance((last_city.x, last_city.y), (city.x, city.y))
                load += city.demand
                last_city = city
            dist += calculate_distance((last_city.x, last_city.y), (depot.x, depot.y))

            # Formata status
            txt_load = f"Carga: {load:.1f} / {fleet.vehicle_capacity:.0f} kg"
            txt_dist = f"Dist: {dist:.1f} / {fleet.vehicle_autonomy:.0f} px"
            txt_route = "Rota: [0] -> " + " -> ".join(map(str, route)) + " -> [0]"

            # Limita tamanho do texto da rota
            if len(txt_route) > 35:
                txt_route = txt_route[:32] + "..."

            screen.blit(
                body_font.render(txt_load, True, (180, 180, 180)),
                (panel_x + 35, vehicle_y + 15),
            )
            screen.blit(
                body_font.render(txt_dist, True, (180, 180, 180)),
                (panel_x + 35, vehicle_y + 28),
            )
            screen.blit(
                body_font.render(txt_route, True, (150, 150, 150)),
                (panel_x + 35, vehicle_y + 41),
            )

            # Status Alerts
            status_labels = []
            if load > fleet.vehicle_capacity:
                status_labels.append(("SOBRECARGA", (255, 50, 50)))
            if dist > fleet.vehicle_autonomy:
                status_labels.append(("AUTONOMIA EXCEDIDA", (255, 50, 50)))
            if not status_labels:
                status_labels.append(("OK", (50, 255, 50)))

            status_x = panel_x + panel_width - 15
            for txt, col in status_labels:
                stat_surf = status_font.render(txt, True, col)
                w = stat_surf.get_width()
                screen.blit(stat_surf, (status_x - w, vehicle_y - 2))

        else:
            screen.blit(
                body_font.render("Não utilizado (Em espera)", True, (100, 100, 100)),
                (panel_x + 35, vehicle_y + 15),
            )

        vehicle_y += 60


def draw_text(
    screen: pygame.Surface, text: str, color: pygame.Color, position: tuple[int, int]
) -> None:
    """Desenha um texto genérico na tela do Pygame.

    Args:
        screen: Superfície do Pygame.
        text: String de texto a ser exibida.
        color: Cor do texto.
        position: Tupla (x, y) de posição na tela.
    """
    pygame.font.init()
    font = pygame.font.SysFont("Arial", 13, bold=True)
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, position)
