from django.db import models

class News(models.Model):
    title = models.CharField(max_length=255)
    image = models.CharField(max_length=255)
    link = models.CharField(max_length=255, unique=True)
    expiry = models.BigIntegerField()

    def __str__(self):
        return self.title


class Prediction(models.Model):
    symbol = models.CharField(max_length=10)
    date = models.DateField()
    close_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('symbol', 'date')
