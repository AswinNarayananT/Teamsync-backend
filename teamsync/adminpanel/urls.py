from django.urls import path
from .views import PlanListCreateView, PlanRetrieveUpdateDeleteView, PlanDeleteView

urlpatterns = [
    path("plans/", PlanListCreateView.as_view(), name="plan-list"),
    path("plans/<int:pk>/", PlanRetrieveUpdateDeleteView.as_view(), name="plan-detail"),
    path("plans/<int:pk>/delete/", PlanDeleteView.as_view(), name="plan-delete"),

]
