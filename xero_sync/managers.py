import re
import time
from datetime import datetime, timedelta
from django.db import models, transaction
from django.utils import timezone

first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


class XeroManager(models.Manager):
    xero_id_field = None
    endpoint_name = None

    def __init__(self, sync_method='since', sync_field='UpdatedDateUTC',
                 xero_id_field=None, endpoint_name=None):
        self.sync_method = sync_method
        self.sync_field = sync_field
        self.xero_id_field = xero_id_field or self.xero_id_field
        self.endpoint_name = endpoint_name or self.endpoint_name
        super().__init__()

    def contribute_to_class(self, model, name):
        super().contribute_to_class(model, name)

        if self.xero_id_field is None:
            self.xero_id_field = model.__name__ + 'ID'

        if self.endpoint_name is None:
            self.endpoint_name = model.__name__.lower() + 's'

    def get_local_field_name(self, xero_field):
        if xero_field == self.xero_id_field:
            return 'id'

        if xero_field.endswith('UTC'):
            xero_field = xero_field[:-3]

        # convert CamelCase to lower_underscore
        s1 = first_cap_re.sub(r'\1_\2', xero_field)
        return all_cap_re.sub(r'\1_\2', s1).lower()

    @property
    def remote(self):
        xero = self.model._meta.app_config.xero
        return getattr(xero, self.endpoint_name)

    def get_last_sync(self):
        local_sync_field = self.get_local_field_name(self.sync_field)
        last_update = self.order_by(local_sync_field).last()
        if last_update is None:
            return None
        return getattr(last_update, local_sync_field)

    def get_updates(self, since=None):
        filter = {'order': self.sync_field}
        last = since or self.get_last_sync()
        if last:
            if self.sync_method == 'since':
                # add a second to date so as not to include last item
                last += timedelta(seconds=1)
            filter.update({self.sync_method: last})

        updates = self.remote.filter(**filter)
        yield from updates

        if len(updates) > 0:
            time.sleep(1)
            last = updates[-1].get(self.sync_field)
            yield from self.get_updates(since=last)

    @transaction.atomic
    def apply_changes(self, record, **extra):
        obj = self.model()
        for key, value in record.items():
            if isinstance(value, datetime):
                value = timezone.make_aware(value)
            setattr(obj, self.get_local_field_name(key), value)
        for key, value in extra:
            setattr(obj, key, value)
        obj.save()
        if hasattr(obj, 'on_sync'):
            obj.on_sync(record)

        return obj

    def sync(self, output=None):
        if self.sync_method is None:
            return

        if output:
            output.write(
                'Syncing {}'.format(self.model._meta.verbose_name_plural))
            output.flush()

        for record in self.get_updates():
            if output:
                output.write('.')
                output.flush()
            self.apply_changes(record)

        output.write('\n')


class TrackingCategoryManager(XeroManager):
    xero_id_field = 'TrackingOptionID'
    endpoint_name = 'trackingcategories'

    def get_updates(self):
        name = self.model.__name__
        categories = self.remote.filter(Name=name)
        if len(categories) > 0:
            return categories[0]['Options']
        return []
