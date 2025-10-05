from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = (
        ("borrower", "Borrower"),
        ("lender", "Lender"),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Loan(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),    
        ("funded", "Funded"),     
        ("completed", "Completed") 
    )

    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="borrowed_loans")
    lender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="lent_loans")

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    period_months = models.PositiveIntegerField(default=6)
    annual_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    lenme_fee = models.DecimalField(max_digits=6, decimal_places=2, default=3.75)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)
    funded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Loan #{self.id} - {self.borrower.username} (${self.amount}) [{self.status}]"


class LoanOffer(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="offers")
    lender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="offers_made")
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Offer by {self.lender.username} for Loan #{self.loan.id} at {self.interest_rate}%"


class Payment(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("paid", "Paid"),
    )

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="payments")
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    def __str__(self):
        return f"Payment for Loan #{self.loan.id} on {self.due_date} - {self.status}"
    @property
    def is_paid(self):
        return self.status == "paid"
