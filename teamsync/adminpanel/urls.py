from django.urls import path
from .views import PlanListCreateView, PlanRetrieveUpdateDeleteView, PlanDeleteView ,AdminWorkspaceListView,PlanAdminStatsAPIView, ToggleBlockWorkspaceView

urlpatterns = [
    path("plans/", PlanListCreateView.as_view(), name="plan-list"),
    path("plans/<int:pk>/", PlanRetrieveUpdateDeleteView.as_view(), name="plan-detail"),
    path("plans/<int:pk>/delete/", PlanDeleteView.as_view(), name="plan-delete"),
    path("workspaces/", AdminWorkspaceListView.as_view(), name="plan-list"),
    path('workspaces/<int:pk>/toggle-block/', ToggleBlockWorkspaceView.as_view()),
    path('plans-stats/', PlanAdminStatsAPIView.as_view(), name='admin-plans-stats'),

]
