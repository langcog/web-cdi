from django.db import models

# Model for stored IP addresses (only stored for studies created by 'langcoglab' and specific studies marked to log IP addresses, under Stanford's IRB approval)
class ip_address(models.Model):
    study = models.ForeignKey(
        "study", on_delete=models.CASCADE
    )  # Study associated with IP address
    ip_address = models.CharField(max_length=30)  # Actual IP address
    date_added = models.DateTimeField(
        verbose_name="Date IP address was added to database", auto_now_add=True
    )  # Date that IP address was added to database.

