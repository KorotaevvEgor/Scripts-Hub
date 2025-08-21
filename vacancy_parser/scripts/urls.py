from django.urls import path
from . import views

app_name = 'scripts'

urlpatterns = [
    path('', views.script_list_view, name='list'),
    path('<int:script_id>/', views.script_detail_view, name='detail'),
    path('<int:script_id>/run/', views.run_script_view, name='run'),
    path('<int:script_id>/export/', views.export_vacancies_excel, name='export_excel'),
    path('run/<int:run_id>/status/', views.script_status_view, name='status'),
    path('run/<int:run_id>/vacancies/', views.vacancies_view, name='vacancies'),
    path('run/<int:run_id>/delete/', views.delete_script_run_view, name='delete_run'),
    path('history/', views.script_history_view, name='history'),
]
