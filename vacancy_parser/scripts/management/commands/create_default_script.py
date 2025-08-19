from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from scripts.models import Script


class Command(BaseCommand):
    help = 'Создает скрипт по умолчанию для всех пользователей'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Создать скрипт только для конкретного пользователя',
        )

    def handle(self, *args, **options):
        if options['user']:
            try:
                user = User.objects.get(username=options['user'])
                users = [user]
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Пользователь {options["user"]} не найден')
                )
                return
        else:
            users = User.objects.all()

        created_count = 0
        for user in users:
            # Проверяем, есть ли уже такой скрипт у пользователя
            if not Script.objects.filter(
                created_by=user, 
                script_type='hh_parser'
            ).exists():
                
                script = Script.objects.create(
                    name='Парсер вакансий "Инженер по охране труда"',
                    description='Парсинг вакансий "Инженер по охране труда" с сайта hh.ru с отслеживанием новых и существующих вакансий',
                    script_type='hh_parser',
                    search_query='Инженер по охране труда',
                    created_by=user,
                    is_active=True
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Создан скрипт "{script.name}" для пользователя {user.username}'
                    )
                )
            else:
                self.stdout.write(
                    f'Пользователь {user.username} уже имеет скрипт парсера hh.ru'
                )

        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Всего создано скриптов: {created_count}')
            )
        else:
            self.stdout.write('Новые скрипты не созданы')
