from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json
from .models import Script, ScriptRun, Vacancy, VacancyRun


@admin.register(Script)
class ScriptAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'script_type', 
        'search_summary_display', 
        'region_display',
        'is_active', 
        'created_by', 
        'allowed_users_count', 
        'created_at'
    ]
    list_filter = ['script_type', 'region', 'is_active', 'created_at']
    search_fields = ['name', 'search_query', 'search_queries', 'description']
    readonly_fields = ['created_at', 'updated_at', 'search_summary_preview']
    filter_horizontal = ['allowed_users']  # Удобный интерфейс для управления M2M связями
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'script_type', 'is_active')
        }),
        ('Настройки поиска', {
            'fields': ('search_queries', 'region', 'max_pages', 'search_summary_preview'),
            'description': 'Настройте поисковые запросы и регион. '
                         'Поисковые запросы задаются в формате JSON массива: ["запрос1", "запрос2"]'
        }),
        ('Совместимость (устаревшее)', {
            'fields': ('search_query',),
            'classes': ('collapse',),
            'description': 'Поле для совместимости со старыми скриптами. Используйте поле "Поисковые запросы" выше.'
        }),
        ('Управление доступом', {
            'fields': ('created_by', 'allowed_users'),
            'description': 'Управляйте пользователями, которые имеют доступ к этому скрипту'
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def search_summary_display(self, obj):
        """Краткое отображение поисковых настроек в списке"""
        try:
            queries = obj.get_search_queries_list()
            if len(queries) == 1:
                return queries[0][:30] + ('...' if len(queries[0]) > 30 else '')
            else:
                return f"{len(queries)} запросов: {queries[0][:20]}..."
        except:
            return "Ошибка в настройках"
    search_summary_display.short_description = 'Поисковые запросы'
    
    def region_display(self, obj):
        """Отображение региона"""
        return obj.get_region_display_name()
    region_display.short_description = 'Регион'
    
    def search_summary_preview(self, obj):
        """Предпросмотр настроек поиска"""
        if obj.pk:  # Только для существующих объектов
            queries = obj.get_search_queries_list()
            region_name = obj.get_region_display_name()
            
            queries_html = "<ul>"
            for query in queries:
                queries_html += f"<li><strong>{query}</strong></li>"
            queries_html += "</ul>"
            
            return format_html(
                '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
                '<strong>Регион:</strong> {}<br>'
                '<strong>Поисковые запросы:</strong><br>{}'
                '</div>',
                region_name,
                mark_safe(queries_html)
            )
        return "Сохранить скрипт для предпросмотра"
    search_summary_preview.short_description = 'Предпросмотр настроек'
    
    def allowed_users_count(self, obj):
        """Отображает количество пользователей с доступом к скрипту"""
        count = obj.get_allowed_users_count()
        if count == 0:
            return format_html('<span style="color: #999;">Нет доступа</span>')
        elif count <= 3:
            # Показываем имена пользователей, если их немного
            names = obj.get_allowed_users_names()
            return format_html('<span style="color: #28a745;">{} ({})</span>', count, names)
        else:
            return format_html('<span style="color: #28a745;">{} пользователей</span>', count)
    
    allowed_users_count.short_description = 'Пользователи с доступом'
    allowed_users_count.admin_order_field = 'allowed_users'
    
    def get_queryset(self, request):
        """Предзагружаем связанные данные для оптимизации"""
        return super().get_queryset(request).select_related('created_by').prefetch_related('allowed_users')


@admin.register(ScriptRun)
class ScriptRunAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'script', 'status_display', 'started_by', 'started_at', 
        'duration', 'total_found', 'new_vacancies', 'queries_info'
    ]
    list_filter = ['status', 'started_at', 'script']
    search_fields = ['script__name', 'started_by__username']
    readonly_fields = ['started_at', 'completed_at', 'queries_stats_display']
    raw_id_fields = ['script', 'started_by']
    date_hierarchy = 'started_at'
    
    fieldsets = (
        ('Запуск', {
            'fields': ('script', 'started_by', 'status')
        }),
        ('Временные метки', {
            'fields': ('started_at', 'completed_at')
        }),
        ('Статистика', {
            'fields': ('total_found', 'new_vacancies', 'existing_vacancies')
        }),
        ('Детальная статистика по запросам', {
            'fields': ('queries_stats_display',),
            'classes': ('collapse',)
        }),
        ('Дополнительно', {
            'fields': ('error_message', 'log_data'),
            'classes': ('collapse',)
        })
    )
    
    def status_display(self, obj):
        """Цветное отображение статуса"""
        colors = {
            'running': '#ffc107',  # Желтый
            'completed': '#28a745',  # Зеленый
            'failed': '#dc3545'  # Красный
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Статус'
    
    def duration(self, obj):
        """Длительность выполнения"""
        if obj.completed_at and obj.started_at:
            duration = obj.completed_at - obj.started_at
            total_seconds = int(duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if hours > 0:
                return f"{hours}ч {minutes}м {seconds}с"
            elif minutes > 0:
                return f"{minutes}м {seconds}с"
            else:
                return f"{seconds}с"
        elif obj.status == 'running':
            return "Выполняется..."
        return "Не завершен"
    duration.short_description = 'Длительность'
    
    def queries_info(self, obj):
        """Краткая информация о поисковых запросах"""
        try:
            stats = obj.get_queries_stats()
            if stats:
                return f"{len(stats)} запросов"
            else:
                queries = obj.script.get_search_queries_list()
                return f"{len(queries)} запросов (старый формат)"
        except:
            return "—"
    queries_info.short_description = 'Запросы'
    
    def queries_stats_display(self, obj):
        """Подробная статистика по запросам"""
        try:
            stats = obj.get_queries_stats()
            if not stats:
                return "Статистика недоступна (возможно, старый формат запуска)"
            
            html = '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
            for query, data in stats.items():
                html += f'<div style="margin-bottom: 10px; padding: 8px; background: white; border-radius: 3px;">'
                html += f'<strong>"{query}":</strong><br>'
                html += f'• Найдено в API: {data.get("total_found", 0)}<br>'
                html += f'• Собрано: {data.get("collected_vacancies", 0)}<br>'
                html += f'• Уникальных: {data.get("unique_vacancies", 0)}<br>'
                html += f'• Новых: {data.get("new_vacancies", 0)}<br>'
                html += f'• Существующих: {data.get("existing_vacancies", 0)}<br>'
                if data.get("duplicates", 0) > 0:
                    html += f'• Дубликатов: {data.get("duplicates", 0)}<br>'
                html += '</div>'
            html += '</div>'
            return mark_safe(html)
        except Exception as e:
            return f"Ошибка отображения статистики: {e}"
    queries_stats_display.short_description = 'Статистика по запросам'


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = [
        'title_short', 'company', 'area_name', 'found_by_query', 
        'script', 'is_active', 'times_found', 'first_seen_at', 'last_seen_at'
    ]
    list_filter = ['is_active', 'script', 'area_name', 'found_by_query', 'first_seen_at', 'company']
    search_fields = ['title', 'company', 'external_id', 'area_name', 'found_by_query']
    readonly_fields = ['first_seen_at', 'last_seen_at', 'times_found']
    raw_id_fields = ['script']
    date_hierarchy = 'first_seen_at'
    
    fieldsets = (
        ('Информация о вакансии', {
            'fields': ('title', 'company', 'salary', 'url', 'published_at')
        }),
        ('Расширенная информация', {
            'fields': ('area_name', 'found_by_query')
        }),
        ('Системная информация', {
            'fields': ('script', 'external_id', 'is_active')
        }),
        ('Статистика отслеживания', {
            'fields': ('first_seen_at', 'last_seen_at', 'times_found'),
            'classes': ('collapse',)
        })
    )
    
    def title_short(self, obj):
        """Короткое название вакансии"""
        title = obj.title
        if len(title) > 60:
            return title[:60] + '...'
        return title
    title_short.short_description = 'Название'
    title_short.admin_order_field = 'title'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('script')


@admin.register(VacancyRun)
class VacancyRunAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'vacancy_title', 'script_name', 'script_run_id', 
        'found_by_query', 'is_new_in_run', 'found_at'
    ]
    list_filter = ['is_new_in_run', 'found_by_query', 'found_at', 'script_run__script']
    search_fields = [
        'vacancy__title', 'vacancy__company', 'script_run__script__name',
        'found_by_query'
    ]
    readonly_fields = ['found_at']
    raw_id_fields = ['script_run', 'vacancy']
    date_hierarchy = 'found_at'
    
    def vacancy_title(self, obj):
        title = obj.vacancy.title
        return title[:50] + ('...' if len(title) > 50 else '')
    vacancy_title.short_description = 'Вакансия'
    
    def script_name(self, obj):
        return obj.script_run.script.name
    script_name.short_description = 'Скрипт'
    
    def script_run_id(self, obj):
        return f"Запуск #{obj.script_run.id}"
    script_run_id.short_description = 'Запуск'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'vacancy', 'script_run', 'script_run__script'
        )


# Дополнительная кастомизация для User модели в админке (опционально)
try:
    from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
    from django.contrib.auth.models import User
    
    # Расширяем стандартную админку пользователей
    class UserAdmin(BaseUserAdmin):
        def get_fieldsets(self, request, obj=None):
            fieldsets = super().get_fieldsets(request, obj)
            if obj:  # При редактировании существующего пользователя
                # Добавляем секцию с доступными скриптами
                accessible_count = obj.accessible_scripts.count()
                created_count = obj.created_scripts.count()
                
                additional_fieldsets = (
                    ('Доступ к скриптам', {
                        'fields': (),
                        'description': format_html(
                            'Создано скриптов: <strong>{}</strong><br>'
                            'Доступ к скриптам: <strong>{}</strong>',
                            created_count, accessible_count
                        )
                    }),
                )
                return fieldsets + additional_fieldsets
            return fieldsets
        
        def get_readonly_fields(self, request, obj=None):
            readonly_fields = list(super().get_readonly_fields(request, obj))
            return readonly_fields

    # Перерегистрируем админку пользователей
    admin.site.unregister(User)
    admin.site.register(User, UserAdmin)
    
except Exception as e:
    # Если что-то пошло не так с перерегистрацией - пропускаем
    print(f"Предупреждение: не удалось расширить админку пользователей: {e}")
    pass
