from __future__ import unicode_literals

from django.db import models
from . import managers


class Account(models.Model):
    id = models.TextField(primary_key=True)
    bank_account_type = models.TextField()
    account_class = models.TextField(db_column='class')
    code = models.TextField()
    name = models.TextField()
    description = models.TextField()
    enable_payments_to_account = models.BooleanField()
    has_attachments = models.BooleanField()
    reporting_code = models.TextField()
    show_in_expense_claims = models.BooleanField()
    status = models.TextField()
    tax_type = models.TextField()
    type = models.TextField()
    updated_date = models.DateTimeField()

    objects = managers.XeroManager()

    def __str__(self):
        return self.name

class Activity(models.Model):
    id = models.TextField(primary_key=True)
    name = models.TextField()
    status = models.TextField()

    objects = managers.TrackingCategoryManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'activities'


class Journal(models.Model):
    id = models.TextField(primary_key=True)
    journal_date = models.DateTimeField()
    journal_number = models.IntegerField()
    created_date = models.DateTimeField()
    reference = models.TextField()
    source_id = models.TextField()
    source_type = models.TextField()

    objects = managers.XeroManager(
        sync_method='offset', sync_field='JournalNumber')

    def __str__(self):
        return (
            '[{0.journal_number}] {0.journal_date:%Y-%m-%d} - {0.reference}'
            .format(self))

    def on_sync(self, record):
        for item in record['JournalLines']:
            JournalLine.objects.apply_changes(item, journal=self)


class JournalLine(models.Model):
    id = models.TextField(primary_key=True)
    journal = models.ForeignKey(Journal, models.PROTECT, related_name='lines')
    account = models.ForeignKey(Account, models.PROTECT,
                                related_name='journal_lines')
    description = models.TextField()
    net_amount = models.DecimalField(max_digits=11, decimal_places=2)
    gross_amount = models.DecimalField(max_digits=11, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=11, decimal_places=2)
    tax_type = models.TextField()
    tax_name = models.TextField()
    activities = models.ManyToManyField(Activity)

    objects = managers.XeroManager(sync_method=None)

    def __str__(self):
        return ('{0.account.name}: {0.gross_amount} ({0.description})'
                .format(self))

    def on_sync(self, record):
        options = (c['TrackingOptionID'] for c in record['TrackingCategories']
                   if c['Name'] == 'Activity')
        self.activities = Activity.objects.filter(id__in=options)
