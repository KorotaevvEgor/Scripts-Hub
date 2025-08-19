from django.contrib import admin
from .models import Script, ScriptRun, Vacancy, VacancyRun


@admin.register(Script)
class ScriptAdmin(admin.ModelAdmin):
    list_display = ['name', 'script_type', 'search_query', 'is_active', 'created_by', 'created_at']
    list_filter = ['script_type', 'is_active', 'created_at']
    search_fields = ['name', 'search_query', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'script_type', 'search_query', 'is_active')
        }),
        ('Системная информация', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ScriptRun)
class ScriptRunAdmin(admin.ModelAdmin):
    list_display = ['id', 'script', 'status', 'started_by', 'started_at', 'completed_at', 'total_found', 'new_vacancies']
    list_filter = ['status', 'started_at', 'script']
    search_fields = ['script__name', 'started_by__username']
    readonly_fields = ['started_at', 'completed_at']
    raw_id_fields = ['script', 'started_by']
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
        ('Дополнительно', {
            'fields': ('error_message', 'log_data'),
            'classes': ('collapse',)
        })
    )


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'script', 'is_active', 'times_found', 'first_seen_at', 'last_seen_at']
    list_filter = ['is_active', 'script', 'first_seen_at', 'company']
    search_fields = ['title', 'company', 'external_id']
    readonly_fields = ['first_seen_at', 'last_seen_at', 'times_found']
    raw_id_fields = ['script']
    date_hierarchy = 'first_seen_at'
    fieldsets = (
        ('Информация о вакансии', {
            'fields': ('title', 'company', 'salary', 'url', 'published_at')
        }),
        ('Системная информация', {
            'fields': ('script', 'external_id', 'is_active')
        }),
        ('Статистика отслеживания', {
            'fields': ('first_seen_at', 'last_seen_at', 'times_found'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('script')


@admin.register(VacancyRun)
class VacancyRunAdmin(admin.ModelAdmin):
    list_display = ['id', 'vacancy_title', 'script_name', 'script_run_id', 'is_new_in_run', 'found_at']
    list_filter = ['is_new_in_run', 'found_at', 'script_run__script']
    search_fields = ['vacancy__title', 'vacancy__company', 'script_run__script__name']
    readonly_fields = ['found_at']
    raw_id_fields = ['script_run', 'vacancy']
    date_hierarchy = 'found_at'
    
    def vacancy_title(self, obj):
        return obj.vacancy.title[:50] + ('...' if len(obj.vacancy.title) > 50 else '')
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
