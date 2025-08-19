from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
import zoneinfo
from .models import Script, ScriptRun, Vacancy, VacancyRun
from .parser import HHVacancyParserDjango
import json
import threading
import datetime


def get_user_scripts_context(request):
    """Контекст-процессор для передачи скриптов пользователя в шаблоны"""
    if request.user.is_authenticated:
        user_scripts = Script.objects.filter(
            created_by=request.user, 
            is_active=True
        ).order_by('name')[:10]  # Ограничиваем 10 скриптами
        return {'user_scripts_menu': user_scripts}
    return {}


def register_view(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Создаем скрипт по умолчанию для нового пользователя
            Script.objects.create(
                name='Парсер Инженер по охране труда',
                description='Парсинг вакансий "Инженер по охране труда" с hh.ru',
                search_query='Инженер по охране труда',
                created_by=user
            )
            login(request, user)
            messages.success(request, 'Регистрация успешно завершена!')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def home_view(request):
    """Главная страница"""
    user_scripts = Script.objects.filter(created_by=request.user, is_active=True)
    recent_runs = ScriptRun.objects.filter(
        script__created_by=request.user
    ).order_by('-started_at')[:5]
    
    # Получаем запуски за сегодня
    # Используем локальную дату для определения сегодняшнего дня
    today_local = timezone.localtime().date()
    
    # Создаем начало и конец дня в локальном часовом поясе
    current_tz = timezone.get_current_timezone()
    start_of_day_local = datetime.datetime.combine(today_local, datetime.time.min, tzinfo=current_tz)
    end_of_day_local = datetime.datetime.combine(today_local, datetime.time.max, tzinfo=current_tz)
    
    # Преобразуем в UTC для сравнения с базой данных
    utc_tz = zoneinfo.ZoneInfo("UTC")
    start_of_day_utc = start_of_day_local.astimezone(utc_tz)
    end_of_day_utc = end_of_day_local.astimezone(utc_tz)

    today_runs_count = ScriptRun.objects.filter(
        script__created_by=request.user,
        started_at__gte=start_of_day_utc,
        started_at__lte=end_of_day_utc
    ).count()
    
    # Получаем статистику новых вакансий из последних запусков каждого скрипта
    new_vacancies_total = 0
    for script in user_scripts:
        last_run = script.runs.filter(status='completed').order_by('-started_at').first()
        if last_run:
            new_vacancies_total += last_run.new_vacancies or 0
    
    # Получаем общее количество уникальных вакансий за всю историю
    total_vacancies = Vacancy.objects.filter(
        script__created_by=request.user
    ).count()
    
    context = {
        'user_scripts': user_scripts,
        'recent_runs': recent_runs,
        'new_vacancies_total': new_vacancies_total,
        'total_vacancies': total_vacancies,
        'today_runs_count': today_runs_count,
    }
    return render(request, 'home.html', context)


@login_required
def script_list_view(request):
    """Список скриптов пользователя"""
    scripts = Script.objects.filter(created_by=request.user, is_active=True)
    return render(request, 'scripts/list.html', {'scripts': scripts})


@login_required
def script_detail_view(request, script_id):
    """Детали скрипта и вакансий"""
    script = get_object_or_404(Script, id=script_id, created_by=request.user)
    
    # Получаем последний запуск
    last_run = script.runs.order_by('-started_at').first()
    
    # Получаем вакансии из последнего запуска
    new_vacancy_runs = []
    old_vacancy_runs = []
    
    if last_run:
        new_vacancy_runs = last_run.vacancy_runs.filter(is_new_in_run=True).select_related('vacancy').order_by('-found_at')
        old_vacancy_runs = last_run.vacancy_runs.filter(is_new_in_run=False).select_related('vacancy').order_by('-found_at')
    
    # Получаем общую статистику по всем вакансиям скрипта
    all_vacancies = script.vacancies.all()
    active_vacancies = all_vacancies.filter(is_active=True)
    
    context = {
        'script': script,
        'last_run': last_run,
        'new_vacancy_runs': new_vacancy_runs,
        'old_vacancy_runs': old_vacancy_runs,
        'total_vacancies': all_vacancies.count(),
        'active_vacancies_count': active_vacancies.count(),
    }
    return render(request, 'scripts/detail.html', context)


@login_required
def run_script_view(request, script_id):
    """Запуск скрипта"""
    if request.method == 'POST':
        script = get_object_or_404(Script, id=script_id, created_by=request.user)
        
        # Проверяем, нет ли активных запусков
        active_run = script.runs.filter(status='running').first()
        if active_run:
            return JsonResponse({
                'success': False, 
                'error': 'Скрипт уже выполняется'
            })
        
        # Создаем новый запуск
        script_run = ScriptRun.objects.create(
            script=script,
            started_by=request.user,
            status='running'
        )
        
        # Запускаем парсер в отдельном потоке
        def run_parser():
            parser = HHVacancyParserDjango(script_run)
            parser.run()
        
        thread = threading.Thread(target=run_parser)
        thread.daemon = True
        thread.start()
        
        return JsonResponse({
            'success': True, 
            'run_id': script_run.id,
            'message': 'Скрипт запущен'
        })
    
    return JsonResponse({'success': False, 'error': 'Неправильный метод запроса'})


@login_required
def script_status_view(request, run_id):
    """Получение статуса выполнения скрипта"""
    try:
        script_run = ScriptRun.objects.get(
            id=run_id, 
            script__created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'status': script_run.status,
            'total_found': script_run.total_found,
            'new_vacancies': script_run.new_vacancies,
            'existing_vacancies': script_run.existing_vacancies,
            'error_message': script_run.error_message,
            'completed_at': script_run.completed_at.isoformat() if script_run.completed_at else None
        })
    except ScriptRun.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Запуск не найден'})


@login_required
def script_history_view(request):
    """История запусков скриптов"""
    runs = ScriptRun.objects.filter(
        script__created_by=request.user
    ).order_by('-started_at')
    
    paginator = Paginator(runs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'scripts/history.html', {'page_obj': page_obj})


@login_required
def vacancies_view(request, run_id):
    """Просмотр вакансий по конкретному запуску"""
    script_run = get_object_or_404(
        ScriptRun, 
        id=run_id, 
        script__created_by=request.user
    )
    
    vacancy_filter = request.GET.get('filter', 'all')
    
    if vacancy_filter == 'new':
        vacancy_runs = script_run.vacancy_runs.filter(is_new_in_run=True)
    elif vacancy_filter == 'existing':
        vacancy_runs = script_run.vacancy_runs.filter(is_new_in_run=False)
    else:
        vacancy_runs = script_run.vacancy_runs.all()
    
    vacancy_runs = vacancy_runs.select_related('vacancy').order_by('-found_at')
    
    paginator = Paginator(vacancy_runs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'script_run': script_run,
        'page_obj': page_obj,
        'current_filter': vacancy_filter,
    }
    return render(request, 'scripts/vacancies.html', context)
