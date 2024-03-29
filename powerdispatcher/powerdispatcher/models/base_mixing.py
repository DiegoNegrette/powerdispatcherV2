from django.db import models


class ModifiedTimeStampMixin(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if "update_fields" in kwargs:
            kwargs["update_fields"] = list(
                set(list(kwargs["update_fields"]) + ["modified"])
            )
        return super(ModifiedTimeStampMixin, self).save(*args, **kwargs)
