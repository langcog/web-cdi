from django.db import models


# Model for stored gift card codes
class PaymentCode(models.Model):
    study = models.ForeignKey(
        "study", on_delete=models.CASCADE
    )  # Associated study name
    hash_id = models.CharField(
        max_length=128, unique=True, null=True
    )  # Populated with hash ID of participant that code was given to. Null until code is rewarded. Uniqueness is enforced (one administration can only have 1 code)
    added_date = models.DateTimeField(
        verbose_name="Date code was added to database", auto_now_add=True
    )  # Date that payment code was first added to database
    assignment_date = models.DateTimeField(
        verbose_name="Date code was given to participant", null=True
    )  # Date that payment code was given to a participant
    PAYMENT_TYPE_CHOICES = [
        ("Amazon", "Amazon"),
        ("Tango", "Tango"),
    ]
    payment_type = models.CharField(
        max_length=50, choices=PAYMENT_TYPE_CHOICES
    )  # Type of gift card code. Currently only 'Amazon' is allowed
    gift_amount = models.DecimalField(
        max_digits=6, decimal_places=2, verbose_name="Monetary value"
    )  # Monetary amount associated with gift card code
    gift_code = models.CharField(max_length=151)  # Gift card code

    class Meta:
        unique_together = (
            "payment_type",
            "gift_code",
        )  # Each object must have a unique combination of code type and the actual gift card code itself

    def __str__(self):
        return f"{self.study} {self.gift_code}"
