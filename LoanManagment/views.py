from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta

from .models import Loan, LoanOffer, Payment, User
from .serializers import LoanSerializer, LoanOfferSerializer, PaymentSerializer


# -------------------------
# Borrower: Create Loan
# -------------------------
class LoanCreateView(generics.ListCreateAPIView):
    """
    Borrower can create a new loan request.
    """
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.role != "borrower":
            raise PermissionError("Only borrowers can create loan requests.")
        serializer.save(borrower=self.request.user)


# -------------------------
# Lender: View Open Loans
# -------------------------
class OpenLoansListView(generics.ListAPIView):
    """
    Lenders can view loans that are pending (no lender assigned).
    """
    serializer_class = LoanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Loan.objects.filter(status="pending", lender__isnull=True)


# -------------------------
# Lender: Submit Offer
# -------------------------
class LoanOfferCreateView(generics.CreateAPIView):
    """
    Lenders can submit offers for open loans.
    """
    serializer_class = LoanOfferSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        lender = self.request.user
        if lender.role != "lender":
            raise PermissionError("Only lenders can submit offers.")
        serializer.save(lender=lender)


# -------------------------
# Borrower: Accept Offer
# -------------------------
class AcceptOfferView(APIView):
    """
    Borrower accepts a lender's offer.
    The system:
    - Checks lender balance
    - Deducts (amount + fee)
    - Updates loan to 'Funded'
    - Creates 6 scheduled payments
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, loan_id):
        try:
            loan = Loan.objects.get(id=loan_id, borrower=request.user)
        except Loan.DoesNotExist:
            return Response({"error": "Loan not found or unauthorized."}, status=status.HTTP_404_NOT_FOUND)

        offer_id = request.data.get("offer_id")
        if not offer_id:
            return Response({"error": "offer_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            offer = LoanOffer.objects.get(id=offer_id, loan=loan)
        except LoanOffer.DoesNotExist:
            return Response({"error": "Offer not found."}, status=status.HTTP_404_NOT_FOUND)

        lender = offer.lender
        total_funding = loan.amount + loan.lenme_fee

        # Check lender balance
        if lender.balance < total_funding:
            return Response({"error": "Insufficient lender balance."}, status=status.HTTP_400_BAD_REQUEST)

        # Deduct amount + fee
        lender.balance -= total_funding
        lender.save()

        # Update loan details
        loan.lender = lender
        loan.annual_interest_rate = offer.interest_rate
        loan.status = "funded"
        loan.funded_at = timezone.now()
        loan.save()

        # Create 6 monthly payments
        monthly_interest_rate = (offer.interest_rate / 100) / 12
        principal = loan.amount
        months = loan.period_months

        # Monthly payment using amortization formula
        monthly_payment = principal * (monthly_interest_rate * (1 + monthly_interest_rate) ** months) / ((1 + monthly_interest_rate) ** months - 1)

        for i in range(months):
            due_date = timezone.now().date() + timedelta(days=30 * (i + 1))
            Payment.objects.create(loan=loan, due_date=due_date, amount=round(monthly_payment, 2))

        return Response({"message": "Offer accepted and loan funded."}, status=status.HTTP_200_OK)


# -------------------------
# Borrower: Make Payment
# -------------------------
class MakePaymentView(APIView):
    """
    Borrower makes a monthly payment.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, loan_id):
        try:
            loan = Loan.objects.get(id=loan_id, borrower=request.user)
        except Loan.DoesNotExist:
            return Response({"error": "Loan not found or unauthorized."}, status=status.HTTP_404_NOT_FOUND)

        payment = loan.payments.filter(status="pending").order_by("due_date").first()
        if not payment:
            return Response({"message": "All payments completed."}, status=status.HTTP_200_OK)

        amount = float(request.data.get("amount", 0))
        if amount < float(payment.amount):
            return Response({"error": f"Payment must be at least {payment.amount}."}, status=status.HTTP_400_BAD_REQUEST)

        # Mark payment as paid
        payment.status = "paid"
        payment.save()

        # Credit lender (principal + interest, ignoring Lenme fee)
        loan.lender.balance += payment.amount
        loan.lender.save()

        # If all payments done → mark loan completed
        if not loan.payments.filter(status="pending").exists():
            loan.status = "completed"
            loan.save()

        return Response({"message": "Payment successful."}, status=status.HTTP_200_OK)