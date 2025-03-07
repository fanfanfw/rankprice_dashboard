from django.db import models
from django.contrib.postgres.fields import ArrayField

class CarCarlistMy(models.Model):
    id = models.IntegerField(primary_key=True)
    listing_url = models.TextField()
    brand = models.CharField(max_length=50, null=True, blank=True)
    model = models.CharField(max_length=50, null=True, blank=True)
    variant = models.CharField(max_length=50, null=True, blank=True)
    informasi_iklan = models.TextField(null=True, blank=True)
    lokasi = models.CharField(max_length=255, null=True, blank=True)
    price = models.CharField(max_length=50, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    millage = models.CharField(max_length=50, null=True, blank=True)
    transmission = models.CharField(max_length=50, null=True, blank=True)
    seat_capacity = models.CharField(max_length=2, null=True, blank=True)

    # Gunakan ArrayField karena kolom di DB adalah text[]
    gambar = ArrayField(
        models.TextField(),
        null=True,
        blank=True
    )

    last_scraped_at = models.DateTimeField(null=True, blank=True)
    version = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'cars'