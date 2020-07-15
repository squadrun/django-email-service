from django.db import models
from django.db.models import Q
from django.db.models.query import QuerySet
from django.utils import timezone


class AbstractQuerySet(QuerySet):
    def update(self, **kwargs):
        if "updated_at" not in kwargs:
            kwargs["updated_at"] = timezone.now()
        return super().update(**kwargs)

    def delete(self):
        return self.update(is_active=False)

    def force_delete(self):
        return super().delete()


class AbstractManager(models.Manager):
    def get_queryset(self, enforce_filter=True):
        qs = AbstractQuerySet(self.model, using=self._db)
        return qs.filter(is_active=True) if enforce_filter else qs

    def unfiltered(self):
        return self.get_queryset(enforce_filter=False)


class AbstractModel(models.Model):
    objects = AbstractManager()

    created_at = models.DateTimeField(
        default=timezone.now,
        help_text="Time of creation of this object",
        editable=False,
    )
    updated_at = models.DateTimeField(
        auto_now=True, help_text="Time of updation of this object", editable=False
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Denotes if the object is active or not. Inactive objects behave similar to how a deleted object "
        "works.",
    )

    class Meta:
        abstract = True
        indexes = [
            models.Index(
                fields=["is_active"],
                condition=Q(is_active=True),
                name="%(class)s_is_active",
            )
        ]

    def update_fields(self, **params):
        self.updated_at = timezone.now()
        update_fields = ["updated_at"]

        for key, value in params.items():
            setattr(self, key, value)
            update_fields.append(key)

        self.save(update_fields=update_fields)

    def delete(self, using=None, keep_parents=False):
        return self.update_fields(is_active=False)
