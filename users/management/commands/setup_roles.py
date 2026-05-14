"""
Management команда для создания групп и назначения прав доступа
Использование: python manage.py setup_roles
"""
from django.core.management.base import BaseCommand
from users.roles import setup_roles


class Command(BaseCommand):
    help = (
        "Создаёт группы пользователей (Администраторы, Менеджеры, Покупатели, "
        "Курьеры, Сборщики) и синхронизирует права доступа"
    )

    def handle(self, *args, **options):
        self.stdout.write('Создание групп и назначение прав доступа...')
        
        try:
            admin_group, manager_group, customer_group, courier_group, picker_group = setup_roles()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n[OK] Группы успешно созданы или обновлены:\n'
                    f'  - {admin_group.name} ({admin_group.permissions.count()} прав)\n'
                    f'  - {manager_group.name} ({manager_group.permissions.count()} прав)\n'
                    f'  - {customer_group.name} ({customer_group.permissions.count()} прав)\n'
                    f'  - {courier_group.name} ({courier_group.permissions.count()} прав)\n'
                    f'  - {picker_group.name} ({picker_group.permissions.count()} прав)'
                )
            )
            
            self.stdout.write(
                self.style.WARNING(
                    '\nДля назначения роли пользователю используйте:\n'
                    '  from users.roles import assign_role_to_user\n'
                    '  assign_role_to_user(user, "admin")  # или "manager", "courier", "customer"'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при создании групп: {e}')
            )

