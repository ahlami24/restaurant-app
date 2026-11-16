# Restaurant Management API

A RESTful backend API for managing a multi-restaurant food ordering platform. Built with **FastAPI** and **PostgreSQL**, the application provides authentication, role-based access control, restaurant and menu management, order processing, and delivery-person management.

The project is designed around multiple user roles and restaurant ownership, with a centralized platform administrator responsible for managing the platform.

## Features

### Authentication and User Management
- User registration and authentication.
- JWT-based authentication.
- Secure password hashing.
- Role-based access control.
- Support for customers, restaurant owners, delivery personnel, and platform administrators.
- User profile management.

### Restaurant Management
- Restaurant registration and management.
- Restaurant owner assignment.
- Restaurant activation and deactivation.
- Restaurant-specific access control.
- Platform administrator access to restaurant information and ownership details.
- Database-level enforcement of one owner per restaurant.

### Menu Management
- Food item creation and management.
- Restaurant-specific food menus.
- Food categorization.
- Food pricing and descriptions.

### Order Management
- Customer order creation.
- Order item and quantity management.
- Automatic order total calculation.
- Order updates and status management.
- Restaurant-specific order management.

### Delivery Management
- Delivery-person management.
- Assignment of delivery personnel to restaurants.
- Access control for delivery-related operations.
- Support for delivery personnel working with multiple restaurants.

### Database and Testing
- PostgreSQL relational database.
- SQLAlchemy ORM for database operations.
- Alembic database migrations.
- Automated tests with pytest.
- Code quality checks with Ruff.
- GitHub Actions continuous integration.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| FastAPI | REST API framework |
| PostgreSQL | Relational database |
| SQLAlchemy | Database ORM |
| Alembic | Database migrations |
| Pydantic | Data validation and serialization |
| JWT | Authentication and access tokens |
| pwdlib | Password hashing |
| Uvicorn | ASGI application server |
| pytest | Automated testing |
| Ruff | Code linting and formatting |
| GitHub Actions | Continuous integration |

## Project Structure

The backend follows a modular structure that separates API routes, database models, schemas, and business logic.

```text
restaurant-app/
│
├── backend/
│   ├── app/
│   │   ├── models/        # Database models
│   │   ├── routes/        # API endpoints
│   │   ├── schemas/       # Request and response schemas
│   │   ├── services/      # Business logic
│   │   ├── database.py    # Database configuration
│   │   └── main.py        # FastAPI application entry point
│   │
│   ├── alembic/           # Database migrations
│   ├── scripts/           # Administrative scripts
│   ├── tests/             # Automated tests
│   └── requirements.txt
│
├── .env.example
└── README.md
```

## Getting Started

Follow these instructions to set up the project locally.

### Prerequisites

Make sure you have the following installed:

- Python 3.10 or newer
- PostgreSQL
- Git
- pip

### 1. Clone the Repository

```bash
git clone https://github.com/ahlami24/restaurant-app.git
cd restaurant-app/backend
```

### 2. Create a Virtual Environment

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a PostgreSQL database:

```sql
CREATE DATABASE restaurant_db;
```

From the repository root, copy the example environment file:

```bash
cp ../.env.example ../.env
```

Edit the .env file and replace the example database credentials with your actual PostgreSQL credentials. Set a strong, randomly generated secret key.

**Important:** Never commit your `.env` file or expose database credentials and secret keys. The repository includes `.env.example` as a configuration reference.

### 5. Run Database Migrations

Make sure PostgreSQL is running and your environment variables are configured.

From the `backend/` directory:

```bash
alembic upgrade head
```

This applies all available database migrations and creates the required database schema.

### 6. Start the Application

Run the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

| Resource | URL |
|---|---|
| API Base URL | http://127.0.0.1:8000 |
| Swagger UI | http://127.0.0.1:8000/docs |
| ReDoc | http://127.0.0.1:8000/redoc |

You can use Swagger UI to explore and interact with the available API endpoints.

### 7. Create the Initial Platform Administrator

The application provides a script for creating the initial platform administrator.

From the `backend/` directory, run:

```bash
python scripts/create_platform_admin.py
```

Follow the script's prompts to create the administrator account.

## Running Tests

The project uses pytest for automated testing.

From the `backend/` directory:

```bash
python -m pytest -q
```

To run tests with more detailed output:

```bash
python -m pytest -v
```

## Code Quality

Ruff is used to check code quality and import organization.

```bash
ruff check .
```

To check and automatically fix supported linting issues:

```bash
ruff check --fix .
```

Review the proposed changes before committing them.

## Database Migrations

Alembic manages database schema changes.

Apply all migrations:

```bash
alembic upgrade head
```

Create a new migration:

```bash
alembic revision --autogenerate -m "describe your changes"
```

Review generated migrations before applying them.

## Security Considerations

- Passwords are stored using secure password hashing.
- Protected endpoints require valid authentication.
- Role-based authorization restricts access to sensitive operations.
- Database credentials and secret keys are stored in environment variables.
- `.env` files must not be committed to version control.
- Database constraints enforce important data integrity rules.

## Continuous Integration

GitHub Actions is used to automatically verify changes through the project's CI workflow.

The workflow runs automated tests and code quality checks to help maintain code reliability and consistency.

## Contributing

Contributions, suggestions, and improvements are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Implement your changes.
4. Add or update tests where appropriate.
5. Run the test suite and code quality checks.
6. Submit a pull request describing your changes.

## Project Repository

**GitHub:** https://github.com/ahlami24/restaurant-app

---

*Built with FastAPI and PostgreSQL.*
