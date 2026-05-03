"""
Motor de simulación del modelo de incendios forestales Drossel–Schwabl.

Estados de celda:
    0 — Vacía
    1 — Árbol
    2 — En llamas
"""

import numpy as np


EMPTY = 0
TREE = 1
FIRE = 2


def create_grid(size: int, initial_density: float = 0.5) -> np.ndarray:
    """
    Crea una cuadrícula inicial con árboles distribuidos aleatoriamente.
    """
    grid = np.zeros((size, size), dtype=np.int8)
    mask = np.random.random((size, size)) < initial_density
    grid[mask] = TREE
    return grid


def _has_burning_neighbor(grid: np.ndarray) -> np.ndarray:
    """
    Calcula una máscara booleana: True donde algún vecino (4-conectado) está en llamas.
    """
    fire = (grid == FIRE)
    # Desplazamientos en los 4 vecinos (arriba, abajo, izquierda, derecha)
    neighbor_fire = (
        np.roll(fire, 1, axis=0)   # vecino de arriba
        | np.roll(fire, -1, axis=0) # vecino de abajo
        | np.roll(fire, 1, axis=1)  # vecino izquierda
        | np.roll(fire, -1, axis=1) # vecino derecha
    )
    return neighbor_fire


def step(grid: np.ndarray, p: float, f: float) -> tuple[np.ndarray, dict]:
    """
    Aplica un paso de simulación según las reglas del modelo Drossel–Schwabl.

    Reglas (aplicadas simultáneamente):
        - Celda vacía  → árbol con probabilidad p.
        - Árbol vecino de llamas → se incendia.
        - Árbol sin vecinos en llamas → se incendia por rayo con probabilidad f.
        - Celda en llamas → vacía.
    """
    size = grid.shape[0]
    rand = np.random.random((size, size))
    neighbor_fire = _has_burning_neighbor(grid)

    new_grid = np.copy(grid)

    # Celdas vacías → árbol con probabilidad p
    empty_mask = (grid == EMPTY)
    new_grid[empty_mask & (rand < p)] = TREE

    # Árboles que se incendian por vecindad o por rayo
    tree_mask = (grid == TREE)
    ignite_by_neighbor = tree_mask & neighbor_fire
    ignite_by_lightning = tree_mask & ~neighbor_fire & (rand < f)
    new_grid[ignite_by_neighbor | ignite_by_lightning] = FIRE

    # Celdas en llamas → vacías
    new_grid[grid == FIRE] = EMPTY

    # Calcular estadísticas: tamaños de incendios iniciados este paso
    newly_ignited = (new_grid == FIRE) & (grid == TREE)
    fire_sizes = _measure_fire_sizes(grid, newly_ignited)

    stats = {
        'fire_sizes': fire_sizes,
        'tree_count': int(np.sum(new_grid == TREE)),
    }

    return new_grid, stats


def _measure_fire_sizes(grid: np.ndarray, newly_ignited: np.ndarray) -> list[int]:
    """
    Estima los tamaños de los incendios que se inician en este paso.

    Usa un BFS simple sobre las celdas actualmente en llamas (grid == FIRE)
    más las recién encendidas para agrupar incendios contiguos.
    """
    # Consideramos "incendio activo" las celdas ya en llamas en el grid anterior
    # más las recién encendidas
    fire_map = (grid == FIRE) | newly_ignited
    visited = np.zeros_like(fire_map, dtype=bool)
    sizes = []
    rows, cols = np.where(fire_map)

    for r, c in zip(rows, cols):
        if visited[r, c]:
            continue
        # BFS
        queue = [(r, c)]
        visited[r, c] = True
        size = 0
        while queue:
            cr, cc = queue.pop()
            size += 1
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = cr + dr, cc + dc
                if (
                    0 <= nr < fire_map.shape[0]
                    and 0 <= nc < fire_map.shape[1]
                    and fire_map[nr, nc]
                    and not visited[nr, nc]
                ):
                    visited[nr, nc] = True
                    queue.append((nr, nc))
        sizes.append(size)

    return sizes


def grid_to_list(grid: np.ndarray) -> list[list[int]]:
    """
    Convierte la cuadrícula NumPy a lista Python para serialización JSON.
    """
    return grid.tolist()


def list_to_grid(data: list[list[int]]) -> np.ndarray:
    """
    Convierte una lista de listas (venida de JSON/DB) a array NumPy.
    """
    return np.array(data, dtype=np.int8)