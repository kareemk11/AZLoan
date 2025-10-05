# AZLoan - P2P Loan Management API 💰🤝

A Django REST API for managing peer-to-peer loans between borrowers and lenders, facilitating the entire loan lifecycle from request to final payment.

---

## ⚙️ System Configuration and Setup

### Requirements

* **Python 3.x**
* **Pipenv** for dependency and environment management
* **SQLite3** database (default configuration)

### Installation Guide

1. **Install Pipenv** globally:

    ```bash
    pip install pipenv
    ```

2. **Clone the Repository**:

    ```bash
    # git clone (https://github.com/kareemk11/AZLoan.git)
    # cd AZLoan
    ```

3. **Create and Activate Virtual Environment**:
    This step installs the environment and activates it for use.

    ```bash
    pipenv install
    pipenv shell
    ```

4. **Install Project Dependencies**:
    The project relies on Django, Django REST Framework, JWT for auth, and Spectacular for documentation.

    ```bash
    pipenv install django djangorestframework djangorestframework-simplejwt drf-spectacular drf-spectacular-sidecar
    ```

5. **Run Database Migrations**:

    ```bash
    python manage.py migrate
    ```

---

## 🔑 Authentication

The API uses **JSON Web Tokens (JWT)** for secure, stateless authentication. All protected endpoints require a valid Access Token in the `Authorization: Bearer <token>` header.

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/token/` | `POST` | Get an **access** and **refresh** token pair using user credentials. |
| `/api/token/refresh/` | `POST` | Get a new access token using a valid refresh token. |

---

## 🧭 API Endpoints and Loan Flow

The system enforces strict role-based access: **Borrowers** initiate loans and make payments; **Lenders** view open loans and submit offers.

### Core Loan Management Endpoints

| Endpoint | Method | User Role | Description |
| :--- | :--- | :--- | :--- |
| **`/api/loans/`** | `POST` | Borrower | Create a new loan request (fields: `amount`, `period_months`). Status is set to 'pending'. |
| **`/api/loans/open/`** | `GET` | Lender | List all open (pending) loans that do not yet have an assigned lender. |
| **`/api/offers/`** | `POST` | Lender | Submit a loan offer (fields: `loan`, `interest_rate`) against a pending loan. |
| **`/api/loans/{loan_id}/accept_offer/`** | `POST` | Borrower | Accept a specific offer (field: `offer_id`). **Triggers funding and payment schedule creation.** |
| **`/api/loans/{loan_id}/pay/`** | `POST` | Borrower | Make a scheduled payment on a funded loan (field: `amount`). |

### Loan Lifecycle

```mermaid
graph TD
    A[Borrower Creates Loan] -->|POST /api/loans/| B[Pending Loan]
    B -->|GET /api/loans/open/| C[Lender Views Loans]
    C -->|POST /api/offers/| D[Lender Makes Offer] 
    D -->|POST /loans/{id}/accept_offer/| E[Borrower Accepts Offer]
    E -->|System: Transfer Funds| F[Loan Funded & Payments Created]
    F -->|POST /loans/{id}/pay/| G[Process Payments]
    G -->|All Payments Done| H[Loan Completed]


## 📝 Business Logic Highlights

    - **Loan Creation:** Only users with the role `borrower` can create loans. The initial status is always `pending`.

**Offer Acceptance:**

- Verifies the lender has sufficient balance.
- Deducts the loan amount plus the `lenme_fee` from the lender's balance.
- Creates all required monthly `Payment` objects using an amortization schedule.
- Updates the loan status to **funded**.


**Payment Processing:**

- Processes payments in chronological order based on `due_date`.
- Updates the lender's balance upon successful payment.
- Marks the loan status as **completed** once all scheduled payments have been processed.

---

## 📚 API Documentation

Once the server is running (`python manage.py runserver`), interactive documentation is available:

- **Swagger UI:** `/api/docs/`
- **ReDoc:** `/api/redoc/`
- **OpenAPI Schema:** `/api/schema/`

---

## ✅ Testing

To ensure integrity of the loan flow and financial transactions, run the comprehensive test suite:

```bash
python manage.py test
```
