from django.db import models
from django.db.models.expressions import F


class ConcurrencyError(Exception):
    pass


class StaleObjectError(ConcurrencyError):
    pass


class OptimisticLockModel(models.Model):
    version = models.IntegerField(default=0)

    def _do_update(self, base_qs, using, pk_val, values, update_fields,
                   forced_update):
        values.append((self._meta.get_field_by_name('version')[0], None,
                       F('version') + 1))
        filtered = base_qs.filter(version=self.version)
        was_updated = super(OptimisticLockModel, self)._do_update(filtered,
            using, pk_val, values, update_fields, forced_update)

        if not was_updated:
            raise StaleObjectError()

        return was_updated

    class Meta():
        abstract = True


class Author(OptimisticLockModel):
    name = models.CharField(max_length=24)

    def __unicode__(self):
        return self.name


class Book(OptimisticLockModel):
    author = models.ForeignKey(Author)
    title = models.CharField(max_length=24)

    def __unicode__(self):
        return self.title