from rest_framework import serializers
from .models import User, Loan, LoanOffer, Payment


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "balance"]


class LoanOfferSerializer(serializers.ModelSerializer):
    lender = UserSerializer(read_only=True)

    class Meta:
        model = LoanOffer
        fields = ["id", "loan", "lender", "interest_rate", "created_at"]
        read_only_fields = ["id", "created_at", "lender"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "loan", "due_date", "amount", "status"]
        read_only_fields = ["id", "status"]


class LoanSerializer(serializers.ModelSerializer):
    borrower = UserSerializer(read_only=True)
    lender = UserSerializer(read_only=True)
    offers = LoanOfferSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Loan
        fields = [
            "id",
            "borrower",
            "lender",
            "amount",
            "period_months",
            "annual_interest_rate",
            "lenme_fee",
            "status",
            "created_at",
            "funded_at",
            "offers",
            "payments",
        ]
        read_only_fields = ["status", "created_at", "funded_at", "offers", "payments"]

    def create(self, validated_data):
        """Assign borrower automatically from request user."""
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["borrower"] = request.user
        return super().create(validated_data)
