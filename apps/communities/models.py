import uuid

from django.db import models


class Community(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=160)
    country_code = models.CharField(max_length=2)
    region = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["name", "country_code", "region", "city"],
                name="unique_community_location",
            )
        ]

    def __str__(self) -> str:
        return self.name
