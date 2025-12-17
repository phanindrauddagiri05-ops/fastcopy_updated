from django.db import models

class Service(models.Model):
    name = models.CharField(max_length=100)
    icon_class = models.CharField(max_length=50, help_text="FontAwesome icon class (e.g., fa-print)")
    description = models.CharField(max_length=255)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=2.00)

    def __str__(self):
        return self.name