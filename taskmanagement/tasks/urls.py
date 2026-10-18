from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('create/', views.task_create, name='task_create'),
    path('<int:pk>/', views.task_detail, name='task_detail'),
    path('<int:pk>/update/', views.task_update, name='task_update'),
    path('<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('<int:pk>/status/', views.update_task_status, name='update_task_status'),
    path('categories/create/', views.category_create, name='category_create'),
    path('progress/', views.progress_tracking, name='progress_tracking'),
    path('dashboard/', views.dashboard, name='dashboard'),
]