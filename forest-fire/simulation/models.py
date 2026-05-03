"""
Modelo Django para almacenar el estado de una simulación de incendios.

Cada simulación tiene un UUID único, la cuadrícula serializada como JSON,
los parámetros p y f, y las estadísticas acumuladas.
"""

import uuid
import json
import numpy as np
from django.db import models

from .engine import create_grid, grid_to_list


class Simulation(models.Model):
    """
    Representa una simulación del modelo Drossel–Schwabl.

    Atributos que se usan ->
        id: UUID autogenerado, usado como identificador público.
        size: Tamaño N de la cuadrícula NxN.
        p: Probabilidad de crecimiento de árbol.
        f: Probabilidad de ignición por rayo.
        grid_data: Cuadrícula serializada como JSON (lista de listas).
        steps: Número de pasos ejecutados acumulados.
        fire_histogram: Histograma de tamaños de incendio {tamaño: frecuencia}.
        created_at: Timestamp de creación.
        updated_at: Timestamp de última actualización.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    size = models.IntegerField()
    p = models.FloatField()
    f = models.FloatField()

    # La cuadrícula se guarda como texto JSON para máxima portabilidad
    grid_data = models.TextField()

    # Estadísticas acumuladas
    steps = models.IntegerField(default=0)
    fire_histogram = models.TextField(default='{}')  # JSON: {size: count}

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Simulation {self.id} ({self.size}x{self.size}, step={self.steps})"

    # ── Helpers para trabajar con NumPy ────────────────────────────────────

    def get_grid(self) -> np.ndarray:
        """Deserializa grid_data y devuelve un array NumPy."""
        from .engine import list_to_grid
        return list_to_grid(json.loads(self.grid_data))

    def set_grid(self, grid: np.ndarray) -> None:
        """Serializa un array NumPy y lo guarda en grid_data."""
        self.grid_data = json.dumps(grid_to_list(grid))

    def get_histogram(self) -> dict:
        """Deserializa el histograma acumulado de tamaños de incendio."""
        return json.loads(self.fire_histogram)

    def update_histogram(self, fire_sizes: list[int]) -> None:
        """
        Actualiza el histograma con los tamaños de incendio de un paso.
        """
        hist = self.get_histogram()
        for size in fire_sizes:
            key = str(size)
            hist[key] = hist.get(key, 0) + 1
        self.fire_histogram = json.dumps(hist)

    def get_tree_density(self) -> float:
        """Calcula la densidad de árboles (fracción de celdas con árbol)."""
        grid = self.get_grid()
        from .engine import TREE
        return float(np.sum(grid == TREE)) / (self.size * self.size)

    @classmethod
    def create_new(cls, size: int, p: float, f: float) -> 'Simulation':
        """
        Fábrica: crea y guarda una simulación nueva con cuadrícula inicial.
        """
        grid = create_grid(size)
        sim = cls(size=size, p=p, f=f)
        sim.set_grid(grid)
        sim.save()
        return sim
