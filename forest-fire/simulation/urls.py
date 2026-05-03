from django.urls import path
from . import views

urlpatterns = [
    # Cliente web
    path('', views.index, name='index'),

    # API REST
    path('api/simulations/', views.SimulationListCreateView.as_view(), name='simulation-list-create'),
    path('api/simulations/<uuid:pk>/', views.SimulationDetailView.as_view(), name='simulation-detail'),
    path('api/simulations/<uuid:pk>/step/', views.SimulationStepView.as_view(), name='simulation-step'),
    path('api/weather/', views.WeatherView.as_view(), name='weather'),
]