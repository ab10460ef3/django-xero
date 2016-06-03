from django.apps import AppConfig
from django.conf import settings
from xero import Xero
from xero.auth import PrivateCredentials


class XeroAppConfig(AppConfig):
    name = 'xero_sync'
    label = 'xero'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def ready(self):
        with open(settings.XERO_CONFIG['private_key_file']) as keyfile:
            rsa_key = keyfile.read()
        credentials = PrivateCredentials(
            settings.XERO_CONFIG['consumer_key'], rsa_key)
        self.xero = Xero(credentials)
        super().ready()
