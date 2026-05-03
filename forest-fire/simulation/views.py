from django.shortcuts import render
"""
Vistas de la API REST para la simulación de incendios forestales.

Endpoints implementados:
    POST   /api/simulations/            — Crear simulación
    GET    /api/simulations/{id}/       — Obtener estado
    POST   /api/simulations/{id}/step/  — Avanzar N pasos
    PATCH  /api/simulations/{id}/       — Modificar p y/o f
    DELETE /api/simulations/{id}/       — Eliminar simulación
    GET    /api/weather/?city={ciudad}  — Parámetros sugeridos por clima
"""

from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Simulation
from .serializers import (
    SimulationCreateSerializer,
    SimulationDetailSerializer,
    SimulationPatchSerializer,
    StepSerializer,
)
from .engine import step
from .weather import get_suggested_params


# <=====> Vista principal (cliente web) <=====>

def index(request):
    """Sirve el cliente web (HTML + Canvas)."""
    return render(request, 'index.html')


# <=====> API: Lista / Creación <=====>

class SimulationListCreateView(APIView):
    """
    GET  /api/simulations/  — Lista todas las simulaciones existentes.
    POST /api/simulations/  — Crea una nueva simulación.
    """

    def get(self, request):
        """
        Devuelve una lista resumida de todas las simulaciones.

        Response 200:
            [{id, size, p, f, steps, tree_density, created_at}, ...]
        """
        simulations = Simulation.objects.all()
        data = [
            {
                'id': str(s.id),
                'size': s.size,
                'p': s.p,
                'f': s.f,
                'steps': s.steps,
                'tree_density': round(s.get_tree_density(), 4),
                'created_at': s.created_at.isoformat(),
            }
            for s in simulations
        ]
        return Response(data)

    def post(self, request):
        """
        Crea una nueva simulación.

        Body params:
            size (int, 20–200): Tamaño N de la cuadrícula NxN.
            p (float, 0–1):     Probabilidad de crecimiento de árbol.
            f (float, 0–1):     Probabilidad de ignición por rayo.

        Response 201: Estado completo de la simulación creada.
        Response 400: Errores de validación.
        """
        serializer = SimulationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        sim = Simulation.create_new(
            size=serializer.validated_data['size'],
            p=serializer.validated_data['p'],
            f=serializer.validated_data['f'],
        )
        return Response(
            SimulationDetailSerializer(sim).data,
            status=status.HTTP_201_CREATED,
        )


# <=====> API: Detalle / Modificación / Eliminación <=====>

class SimulationDetailView(APIView):
    """
    GET    /api/simulations/{id}/  — Estado actual de la simulación.
    PATCH  /api/simulations/{id}/  — Modifica p y/o f en caliente.
    DELETE /api/simulations/{id}/  — Elimina la simulación.
    """

    def get(self, request, pk):
        """
        Devuelve el estado completo de una simulación.

        Path params:
            pk (UUID): Identificador de la simulación.

        Response 200: {id, size, p, f, grid, steps, tree_density, fire_histogram, ...}
        Response 404: Simulación no encontrada.
        """
        sim = get_object_or_404(Simulation, pk=pk)
        return Response(SimulationDetailSerializer(sim).data)

    def patch(self, request, pk):
        """
        Modifica p y/o f de una simulación en caliente sin reiniciarla.

        Path params:
            pk (UUID): Identificador de la simulación.

        Body params (opcionales):
            p (float, 0–1): Nueva probabilidad de crecimiento.
            f (float, 0–1): Nueva probabilidad de ignición por rayo.

        Response 200: Estado actualizado de la simulación.
        Response 400: Valores fuera de rango.
        Response 404: Simulación no encontrada.
        """
        sim = get_object_or_404(Simulation, pk=pk)
        serializer = SimulationPatchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if 'p' in serializer.validated_data:
            sim.p = serializer.validated_data['p']
        if 'f' in serializer.validated_data:
            sim.f = serializer.validated_data['f']
        sim.save()

        return Response(SimulationDetailSerializer(sim).data)

    def delete(self, request, pk):
        """
        Elimina permanentemente una simulación.

        Path params:
            pk (UUID): Identificador de la simulación.

        Response 204: Sin contenido (eliminación correcta).
        Response 404: Simulación no encontrada.
        """
        sim = get_object_or_404(Simulation, pk=pk)
        sim.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# <=====> API -> Avance de pasos <=====>

class SimulationStepView(APIView):
    """
    POST /api/simulations/{id}/step/  — Avanza N pasos la simulación.
    """

    def post(self, request, pk):
        """
        Avanza la simulación un número determinado de pasos.

        Se usa POST porque esta operación MUTA el estado del servidor, esto
        modifica la cuadrícula, incrementa el contador de pasos y actualiza
        el histograma. GET es idempotente y seguro; POST no lo es, y aquí
        cada llamada produce un resultado diferente y tiene efectos secundarios.

        Path params:
            pk (UUID): Identificador de la simulación.

        Body params:
            steps (int, 1–1000): Número de pasos a ejecutar (por defecto 1).

        Response 200: {id, size, p, f, grid, steps, tree_density, fire_histogram, ...}
        Response 400: Parámetro steps inválido.
        Response 404: Simulación no encontrada.
        """
        sim = get_object_or_404(Simulation, pk=pk)
        serializer = StepSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        n_steps = serializer.validated_data['steps']
        grid = sim.get_grid()

        for _ in range(n_steps):
            grid, stats = step(grid, sim.p, sim.f)
            sim.update_histogram(stats['fire_sizes'])

        sim.set_grid(grid)
        sim.steps += n_steps
        sim.save()

        return Response(SimulationDetailSerializer(sim).data)


# <=====> API: Weather <=====>

class WeatherView(APIView):
    """
    GET /api/weather/?city={ciudad}  — Parámetros sugeridos según el tiempo.
    """

    def get(self, request):
        """
        Consulta la API Open-Meteo para una ciudad y devuelve p y f sugeridos.

        La petición a Open-Meteo se realiza SIEMPRE desde el servidor Django,
        nunca desde el JavaScript del cliente.

        Query params:
            city (str): Nombre de la ciudad (p.ej. "Madrid", "Barcelona").

        Response 200:
            {
                "p": float,
                "f": float,
                "reasoning": str,
                "weather": {
                    "temperature": float,
                    "humidity": float,
                    "wind_speed": float
                }
            }
        Response 400: Falta el parámetro city o la ciudad no existe.
        Response 503: Error al contactar con Open-Meteo.
        """
        city = request.query_params.get('city', '').strip()
        if not city:
            return Response(
                {'error': 'El parámetro city es obligatorio.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = get_suggested_params(city)
            return Response(result)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {'error': f'Error al contactar con Open-Meteo: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
