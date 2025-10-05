from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from django.utils import timezone
from .models import User, Loan, Payment, LoanOffer


class LoanFlowTests(APITestCase):
    def setUp(self):
        # Create borrower and lender users
        self.borrower = User.objects.create_user(
            username="borrower", password="test123", role="borrower", balance=0
        )
        self.lender = User.objects.create_user(
            username="lender", password="test123", role="lender", balance=Decimal("6000.00")
        )

        # Get JWT tokens for both
        self.borrower_token = self._get_jwt_token("borrower", "test123")
        self.lender_token = self._get_jwt_token("lender", "test123")

    def _get_jwt_token(self, username, password):
        """Helper function to retrieve a JWT access token."""
        url = reverse("token_obtain_pair")  # typically /api/token/
        response = self.client.post(url, {"username": username, "password": password}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        return response.data["access"]

    def _auth_as(self, role):
        """Switch authentication header between borrower and lender."""
        if role == "borrower":
            token = self.borrower_token
        elif role == "lender":
            token = self.lender_token
        else:
            raise ValueError("Unknown role")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_full_loan_flow(self):
        """
        Full integration test:
        Borrower requests loan -> Lender offers -> Borrower accepts -> Loan funded -> Payments created and paid
        """

        # 1️⃣ Borrower requests loan
        self._auth_as("borrower")
        loan_data = {"amount": 5000, "term_months": 6}
        response = self.client.post(reverse("loan-list-create"), loan_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        loan_id = response.data["id"]

        loan = Loan.objects.get(id=loan_id)
        self.assertEqual(loan.status.lower(), "pending")

        # 2️⃣ Lender retrieves pending loans
        self._auth_as("lender")
        response = self.client.get(reverse("open-loans"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(l["id"] == loan_id for l in response.data))

        # 3️⃣ Lender submits an offer
        offer_data = {"loan": loan_id, "interest_rate": 15.0}
        response = self.client.post(reverse("create-offer"), offer_data, format="json")
        print("DEBUG Loan Create:", response.status_code, response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        offer_id = response.data["id"]
        loan_id = response.data["loan"]

        # 4️⃣ Borrower accepts offer
        self._auth_as("borrower")
        response = self.client.post(
            reverse("accept-offer", kwargs={"loan_id": offer_id}),{ "offer_id": offer_id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        loan.refresh_from_db()
        self.assertEqual(loan.status.lower(), "funded")

        # 5️⃣ Check lender balance after funding
        self.lender.refresh_from_db()
        self.assertLess(self.lender.balance, Decimal("6000.00"))

        # 6️⃣ Verify that payments are created
        payments = Payment.objects.filter(loan=loan)
        self.assertEqual(payments.count(), 6)

        # 7️⃣ Borrower makes payments
        for p in payments:
            response = self.client.post(
                reverse("make-payment", kwargs={"loan_id": loan_id}),{
                "amount": str(p.amount)
                } ,format="json"
            )
            print("DEBUG Payment Make:", response.status_code, response.data)
            print("DEBUG Payment:", p.id, p.amount, p.status)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            p.refresh_from_db()
            self.assertTrue(p.is_paid)

        # 8️⃣ Verify loan is completed
        loan.refresh_from_db()
        self.assertEqual(loan.status.lower(), "completed")
