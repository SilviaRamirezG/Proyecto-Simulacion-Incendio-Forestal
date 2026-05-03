"""
Serializers de Django REST Framework para la API de simulaciones.
"""

# simulation/serializers.py
import json
from rest_framework import serializers
from .models import Simulation


class SimulationCreateSerializer(serializers.Serializer):
    size = serializers.IntegerField(min_value=20, max_value=200)
    p = serializers.FloatField(min_value=0.0, max_value=1.0)
    f = serializers.FloatField(min_value=0.0, max_value=1.0)


class SimulationPatchSerializer(serializers.Serializer):
    p = serializers.FloatField(min_value=0.0, max_value=1.0, required=False)
    f = serializers.FloatField(min_value=0.0, max_value=1.0, required=False)


class StepSerializer(serializers.Serializer):
    steps = serializers.IntegerField(min_value=1, max_value=1000, default=1)


class SimulationDetailSerializer(serializers.ModelSerializer):
    grid = serializers.SerializerMethodField()
    fire_histogram = serializers.SerializerMethodField()
    tree_density = serializers.SerializerMethodField()

    class Meta:
        model = Simulation
        fields = [
            'id', 'size', 'p', 'f',
            'grid', 'steps',
            'tree_density', 'fire_histogram',
            'created_at', 'updated_at',
        ]

    def get_grid(self, obj):
        return json.loads(obj.grid_data)

    def get_fire_histogram(self, obj):
        raw = json.loads(obj.fire_histogram)
        return {int(k): v for k, v in raw.items()}

    def get_tree_density(self, obj):
        return round(obj.get_tree_density(), 4)