from django.db import models
from model_utils.models import TimeStampedModel

from powerdispatcher.models import Branch, Date, ModifiedTimeStampMixin, Source


class Expense(ModifiedTimeStampMixin, TimeStampedModel):
    id = models.AutoField(primary_key=True)
    date = models.ForeignKey(Date, on_delete=models.PROTECT)
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    source = models.ForeignKey(Source, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=7, decimal_places=2)

    class Meta:
        verbose_name_plural = 'Expenses'
        ordering = ('-date',)

    def __str__(self):
        return f"{self.branch.name} - {self.source.name} - {self.amount}"
