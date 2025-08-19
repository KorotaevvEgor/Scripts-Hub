from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Script(models.Model):
    """Модель для хранения информации о скриптах парсинга"""
    SCRIPT_TYPES = [
        ('hh_parser', 'HeadHunter Parser'),
        ('other', 'Other')
    ]
    
    name = models.CharField(max_length=200, verbose_name='Название скрипта')
    description = models.TextField(verbose_name='Описание')
    script_type = models.CharField(
        max_length=50, 
        choices=SCRIPT_TYPES, 
        default='hh_parser',
        verbose_name='Тип скрипта'
    )
    search_query = models.CharField(
        max_length=200, 
        default='Инженер по охране труда',
        verbose_name='Поисковый запрос'
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
        verbose_name='Создан пользователем'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Скрипт'
        verbose_name_plural = 'Скрипты'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


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
    
    class Meta:
        verbose_name = 'Запуск скрипта'
        verbose_name_plural = 'Запуски скриптов'
        ordering = ['-started_at']
    
    def __str__(self):
        return f'{self.script.name} - {self.started_at.strftime("%d.%m.%Y %H:%M")}'


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
    
    def mark_as_found(self):
        """Отмечает вакансию как найденную в текущем запуске"""
        self.is_active = True
        self.last_seen_at = timezone.now()
        self.times_found += 1
        self.save(update_fields=['is_active', 'last_seen_at', 'times_found'])
        
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
    
    class Meta:
        verbose_name = 'Вакансия в запуске'
        verbose_name_plural = 'Вакансии в запусках'
        unique_together = ['script_run', 'vacancy']
    
    def __str__(self):
        return f'{self.vacancy.title} (Запуск {self.script_run.id})'
