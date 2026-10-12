# Restaurant Management API

A restaurant management backend built with **FastAPI**, **PostgreSQL**,
and **SQLAlchemy**.

## Features

-   User registration and authentication
-   JWT-based authentication
-   Role-based access for customers, restaurant owners, and delivery
    personnel
-   Customer management
-   Food menu management
-   Order creation and management
-   Order status updates
-   Database migrations with Alembic

## Technologies

-   Python
-   FastAPI
-   PostgreSQL
-   SQLAlchemy
-   Alembic
-   JWT authentication

## Prerequisites

Install the following before starting:

-   Python 3.10 or newer
-   PostgreSQL
-   Git

## Setup and Installation

### 1. Clone the repository

``` bash
git clone https://github.com/ahlami24/restaurant-app.git
cd restaurant-app/backend
```

### 2. Create and activate a virtual environment

Linux or macOS:

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

``` powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

``` bash
pip install -r requirements.txt
```

### 4. Configure PostgreSQL and environment variables

Create a PostgreSQL database (for example, `restaurant_db`).

Create a file named `.env` inside the `backend` directory with the
following variables. Replace the example values with your own PostgreSQL
username and password, and generate a strong secret key.

``` env
DATABASE_URL=postgresql://YOUR_DB_USER:YOUR_DB_PASSWORD@localhost:5432/restaurant_db
SECRET_KEY=YOUR_SECRET_KEY
```

Do not commit `.env` to Git. Keep database credentials and secret keys
private.

### 5. Run database migrations

Make sure PostgreSQL is running and your `.env` file is configured. From
the `backend` directory, run:

``` bash
alembic upgrade head
```

### 6. Start the API server

From the `backend` directory, run:

``` bash
uvicorn app.main:app --reload
```

The API should now be available at:

-   API base URL: http://127.0.0.1:8000
-   Interactive API docs: http://127.0.0.1:8000/docs
-   Alternative API docs: http://127.0.0.1:8000/redoc

### 7. Create a restaurant-owner account (optional)

To create an owner account, open another terminal, activate the virtual
environment, and run these commands from the repository root:

``` bash
cd restaurant-app/backend
source .venv/bin/activate
python create_owner.py
```

On Windows PowerShell, activate the virtual environment with:

``` powershell
.venv\Scripts\Activate.ps1
```

Follow the prompts to enter the owner's name, phone number, and
password.

## Troubleshooting

-   **Database connection errors:** Check that PostgreSQL is running and
    that `DATABASE_URL` matches your database name, username, password,
    host, and port.
-   **Missing dependencies:** Confirm the virtual environment is active,
    then run `pip install -r requirements.txt`.
-   **Missing environment variables:** Confirm `backend/.env` contains
    both `DATABASE_URL` and `SECRET_KEY`.

## Security Notes

-   Never commit `.env` or other files containing credentials.
-   Use a strong, private `SECRET_KEY`.
-   Use a separate database for development and production.

## Repository

GitHub: https://github.com/ahlami24/restaurant-app
