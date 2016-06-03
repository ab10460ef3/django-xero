import sys
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Sync database with Xero'

    def add_arguments(self, parser):
        # parser.add_argument('poll_id', nargs='+', type=int)
        pass

    def handle(self, *args, **options):
        from django.apps import apps

        for model in apps.get_app_config('xero').get_models():
            if hasattr(model.objects, 'sync'):
                model.objects.sync(output=sys.stdout)
            self.stdout.write('\n')

        self.stdout.write(self.style.SUCCESS('Sync successful.'))
