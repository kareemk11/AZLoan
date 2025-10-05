

from django.urls import path
from .views import (
    LoanCreateView,
    OpenLoansListView,
    LoanOfferCreateView,
    AcceptOfferView,
    MakePaymentView,
)

urlpatterns = [
    path("loans/", LoanCreateView.as_view(), name="loan-list-create"),
    path("loans/open/", OpenLoansListView.as_view(), name="open-loans"),
    path("offers/", LoanOfferCreateView.as_view(), name="create-offer"),
    path("loans/<int:loan_id>/accept_offer/", AcceptOfferView.as_view(), name="accept-offer"),
    path("loans/<int:loan_id>/pay/", MakePaymentView.as_view(), name="make-payment"),
]
