from django.db import models
import json

class Car(models.Model):
    id = models.AutoField(primary_key=True)
    listing_url = models.TextField(unique=True)
    brand = models.CharField(max_length=50, null=True, blank=True)
    model = models.CharField(max_length=50, null=True, blank=True)
    variant = models.CharField(max_length=50, null=True, blank=True)
    informasi_iklan = models.TextField(null=True, blank=True)
    lokasi = models.CharField(max_length=255, null=True, blank=True)
    price = models.IntegerField(null=True, blank=True)      # Sudah integer
    year = models.IntegerField(null=True, blank=True)
    millage = models.IntegerField(null=True, blank=True)    # Sudah integer
    transmission = models.CharField(max_length=50, null=True, blank=True)
    seat_capacity = models.CharField(max_length=2, null=True, blank=True)
    gambar = models.JSONField(null=True, blank=True)
    last_scraped_at = models.DateTimeField(null=True, blank=True)
    version = models.IntegerField(null=True, blank=True, default=1)
    source = models.CharField(max_length=50, null=True, blank=True)

    def get_first_image(self):
        """Mengambil satu gambar pertama dari JSON atau list"""
        if self.gambar:
            # Jika gambar adalah list Python langsung
            if isinstance(self.gambar, list):
                return self.gambar[0] if len(self.gambar) > 0 else None
            # Jika gambar adalah string JSON, decode dulu
            try:
                images = json.loads(self.gambar)
                return images[0] if len(images) > 0 else None
            except json.JSONDecodeError:
                return None
        return None

    class Meta:
        db_table = "cars"

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"
    

class CarBrand(models.Model):
    id = models.AutoField(primary_key=True)
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)

    class Meta:
        db_table = "cars_brand"
        unique_together = ("brand", "model")  # Mencegah duplikasi brand dan model yang sama

    def __str__(self):
        return f"{self.brand} {self.model}"
