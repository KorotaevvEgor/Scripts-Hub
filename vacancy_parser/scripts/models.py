from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class Script(models.Model):
    """Модель для хранения информации о скриптах парсинга"""
    SCRIPT_TYPES = [
        ('hh_parser', 'HeadHunter Parser'),
        ('other', 'Other')
    ]
    
    REGION_CHOICES = [
        ('1', 'Москва'),
        ('2', 'Санкт-Петербург'),
        ('1002', 'Московская область'),
        ('2019', 'Ленинградская область'),
        ('moscow_mo', 'Москва и МО'),  # Специальная опция для Москвы + МО
        ('all', 'Вся Россия'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Название скрипта')
    description = models.TextField(verbose_name='Описание')
    script_type = models.CharField(
        max_length=50, 
        choices=SCRIPT_TYPES, 
        default='hh_parser',
        verbose_name='Тип скрипта'
    )
    
    # Поле для старых скриптов (deprecated, но сохраняем для совместимости)
    search_query = models.CharField(
        max_length=200, 
        default='Инженер по охране труда',
        verbose_name='Поисковый запрос (устаревшее)',
        help_text='Используется для совместимости со старыми скриптами'
    )
    
    # Новые поля для расширенного поиска
    search_queries = models.TextField(
        default='["Инженер по охране труда", "Специалист по охране труда"]',
        verbose_name='Поисковые запросы (JSON)',
        help_text='JSON массив поисковых запросов, например: ["запрос1", "запрос2"]'
    )
    
    region = models.CharField(
        max_length=20,
        choices=REGION_CHOICES,
        default='moscow_mo',
        verbose_name='Регион поиска',
        help_text='Регион для поиска вакансий'
    )
    
    max_pages = models.PositiveIntegerField(
        default=20,
        verbose_name='Максимальное количество страниц',
        help_text='Максимальное количество страниц для загрузки (по умолчанию 20 - лимит API HH.ru)'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активный')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='Создан пользователем',
        related_name='created_scripts'
    )
    # Поле для управления доступом пользователей
    allowed_users = models.ManyToManyField(
        User,
        blank=True,
        verbose_name='Пользователи с доступом',
        help_text='Пользователи, которые имеют доступ к этому скрипту',
        related_name='accessible_scripts'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Скрипт'
        verbose_name_plural = 'Скрипты'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_search_queries_list(self):
        """Возвращает список поисковых запросов"""
        try:
            queries = json.loads(self.search_queries)
            if isinstance(queries, list) and queries:
                return queries
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Fallback к старому формату
        if self.search_query:
            return [self.search_query]
        
        return ['Инженер по охране труда', 'Специалист по охране труда']
    
    def set_search_queries_list(self, queries_list):
        """Устанавливает список поисковых запросов"""
        if isinstance(queries_list, list):
            self.search_queries = json.dumps(queries_list, ensure_ascii=False)
        else:
            raise ValueError("queries_list должен быть списком")
    
    def get_region_ids(self):
        """Возвращает список ID регионов для API HH.ru"""
        region_mapping = {
            '1': ['1'],  # Москва
            '2': ['2'],  # Санкт-Петербург
            '1002': ['1002'],  # Московская область
            '2019': ['2019'],  # Ленинградская область
            'moscow_mo': ['1', '1002'],  # Москва и МО
            'all': [],  # Вся Россия (без фильтра)
        }
        return region_mapping.get(self.region, ['1', '1002'])
    
    def get_region_display_name(self):
        """Возвращает человекочитаемое название региона"""
        for choice_value, choice_name in self.REGION_CHOICES:
            if choice_value == self.region:
                return choice_name
        return 'Неизвестный регион'
    
    def get_search_summary(self):
        """Возвращает краткое описание поисковых настроек"""
        queries = self.get_search_queries_list()
        queries_str = ', '.join(queries[:2])  # Показываем первые 2 запроса
        if len(queries) > 2:
            queries_str += f' и еще {len(queries) - 2}'
        
        return f'{queries_str} в регионе "{self.get_region_display_name()}"'
    
    def has_access(self, user):
        """Проверяет, имеет ли пользователь доступ к скрипту"""
        if not user.is_authenticated:
            return False
        
        # Создатель всегда имеет доступ
        if self.created_by == user:
            return True
        
        # Суперпользователи имеют доступ ко всем скриптам
        if user.is_superuser:
            return True
        
        # Проверяем, находится ли пользователь в списке разрешенных
        return self.allowed_users.filter(id=user.id).exists()
    
    def get_allowed_users_count(self):
        """Возвращает количество пользователей с доступом к скрипту"""
        return self.allowed_users.count()
    
    def get_allowed_users_names(self):
        """Возвращает список имен пользователей с доступом к скрипту"""
        return ', '.join([user.username for user in self.allowed_users.all()[:5]])


class ScriptRun(models.Model):
    """Модель для хранения истории запусков скриптов"""
    STATUS_CHOICES = [
        ('running', 'Выполняется'),
        ('completed', 'Завершен'),
        ('failed', 'Ошибка'),
    ]
    
    script = models.ForeignKey(
        Script, 
        on_delete=models.CASCADE, 
        related_name='runs',
        verbose_name='Скрипт'
    )
    started_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='Запущен пользователем'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='running',
        verbose_name='Статус'
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Время запуска')
    completed_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name='Время завершения'
    )
    total_found = models.IntegerField(
        default=0, 
        verbose_name='Всего найдено'
    )
    new_vacancies = models.IntegerField(
        default=0, 
        verbose_name='Новых вакансий'
    )
    existing_vacancies = models.IntegerField(
        default=0, 
        verbose_name='Существующих вакансий'
    )
    error_message = models.TextField(
        blank=True, 
        verbose_name='Сообщение об ошибке'
    )
    log_data = models.TextField(
        blank=True, 
        verbose_name='Лог выполнения'
    )
    
    # Новые поля для статистики по запросам
    queries_stats = models.TextField(
        blank=True,
        verbose_name='Статистика по запросам',
        help_text='JSON с детальной статистикой по каждому поисковому запросу'
    )
    
    class Meta:
        verbose_name = 'Запуск скрипта'
        verbose_name_plural = 'Запуски скриптов'
        ordering = ['-started_at']
    
    def __str__(self):
        return f'{self.script.name} - {self.started_at.strftime("%d.%m.%Y %H:%M")}'
    
    def get_queries_stats(self):
        """Возвращает статистику по запросам"""
        try:
            if self.queries_stats:
                return json.loads(self.queries_stats)
        except (json.JSONDecodeError, TypeError):
            pass
        return {}
    
    def set_queries_stats(self, stats_dict):
        """Устанавливает статистику по запросам"""
        if isinstance(stats_dict, dict):
            self.queries_stats = json.dumps(stats_dict, ensure_ascii=False)
        else:
            raise ValueError("stats_dict должен быть словарем")


class Vacancy(models.Model):
    """Модель для хранения информации о вакансиях"""
    # Связь со скриптом (владельцем)
    script = models.ForeignKey(
        Script,
        on_delete=models.CASCADE,
        related_name='vacancies',
        verbose_name='Скрипт'
    )
    
    # Основная информация о вакансии
    external_id = models.CharField(
        max_length=100, 
        verbose_name='Внешний ID'
    )
    title = models.CharField(max_length=500, verbose_name='Название')
    company = models.CharField(max_length=300, verbose_name='Компания')
    salary = models.CharField(max_length=200, verbose_name='Зарплата')
    url = models.URLField(verbose_name='Ссылка на вакансию')
    published_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name='Дата публикации'
    )
    
    # Новые поля для расширенной информации
    area_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Регион',
        help_text='Название региона/города'
    )
    
    found_by_query = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Найдено по запросу',
        help_text='Поисковый запрос, по которому найдена вакансия'
    )
    
    # Метаданные
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активная (ещё существует на сайте)'
    )
    first_seen_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Первое обнаружение'
    )
    last_seen_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Последнее обнаружение'
    )
    times_found = models.PositiveIntegerField(
        default=1,
        verbose_name='Количество обнаружений'
    )
    
    class Meta:
        verbose_name = 'Вакансия'
        verbose_name_plural = 'Вакансии'
        ordering = ['-last_seen_at']
        unique_together = ['script', 'external_id']
    
    def mark_as_found(self, found_by_query=''):
        """Отмечает вакансию как найденную в текущем запуске"""
        self.is_active = True
        self.last_seen_at = timezone.now()
        self.times_found += 1
        if found_by_query:
            self.found_by_query = found_by_query
        self.save(update_fields=['is_active', 'last_seen_at', 'times_found', 'found_by_query'])
        
    def __str__(self):
        return f"{self.title} - {self.company}"


class VacancyRun(models.Model):
    """Модель связи вакансий с конкретным запуском"""
    script_run = models.ForeignKey(
        ScriptRun, 
        on_delete=models.CASCADE, 
        related_name='vacancy_runs',
        verbose_name='Запуск скрипта'
    )
    vacancy = models.ForeignKey(
        Vacancy,
        on_delete=models.CASCADE,
        related_name='runs',
        verbose_name='Вакансия'
    )
    is_new_in_run = models.BooleanField(
        default=True,
        verbose_name='Новая в этом запуске'
    )
    found_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Найдена в запуске'
    )
    
    # Дополнительная информация о том, как найдена вакансия
    found_by_query = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Найдено по запросу',
        help_text='Поисковый запрос, по которому найдена вакансия в этом запуске'
    )
    
    class Meta:
        verbose_name = 'Вакансия в запуске'
        verbose_name_plural = 'Вакансии в запусках'
        unique_together = ['script_run', 'vacancy']
    
    def __str__(self):
        return f'{self.vacancy.title} (Запуск {self.script_run.id})'
