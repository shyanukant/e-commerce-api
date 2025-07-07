# {{ app_name|default:'Your App' }} - Django E-commerce Backend

A modern, production-ready Django REST API backend for the {{ app_name|default:'Your App' }} e-commerce platform.

---

## Features

- **Product Management**: Categories, sizes, products, images, reviews
- **User Authentication**: JWT-based registration, login, profile, and permissions
- **Shopping Cart & Orders**: Add/update/remove items, checkout, order tracking
- **Payment Integration**: Stripe payments with secure webhooks
- **PDF Reports**: Download order receipts and monthly revenue reports (WeasyPrint)
- **Email Campaigns**: Send rich, template-based emails to all users (with WYSIWYG editing)
- **Admin Panel**: Jazzmin-powered, analytics dashboard, custom branding, dark mode
- **Staff Permissions**: Staff group can read/add/update but not delete (products, orders, campaigns)
- **Real-time Updates**: WebSocket support for order status
- **Modern, DRY, and Clean Codebase**

---

## Tech Stack
- Django 5.2+
- Django REST Framework
- SimpleJWT (auth)
- Channels (WebSocket)
- Stripe
- WeasyPrint (PDF)
- django-summernote (WYSIWYG email templates)
- Jazzmin (admin UI)

---

## Setup

### Prerequisites
- Python 3.8+
- pip
- Node.js (for frontend, optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/shyanukant/e-commerce-api.git
   cd e-commerce-api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Collect static files**
   ```bash
   python manage.py collectstatic --noinput
   ```

7. **Run the server**
   ```bash
   python manage.py runserver
   ```

---

## Admin Panel
- Access at: `http://localhost:8000/admin/`
- Jazzmin theme, custom branding, analytics dashboard
- PDF download for order receipts and monthly revenue
- Email campaign management (visual + code editor)
- Staff group: assign users for limited admin permissions (no delete)

---

## API Endpoints (Sample)

### Auth
- `POST /api/users/register/` — Register
- `POST /api/users/login/` — Login
- `POST /api/token/` — JWT token
- `POST /api/token/refresh/` — Refresh token

### Store
- `GET /api/store/products/` — List products
- `POST /api/store/products/` — Add product (admin/staff)
- ...

### Orders
- `GET /api/orders/orders/` — List user orders
- `POST /api/orders/checkout/` — Checkout
- `GET /api/orders/orders/{id}/download_receipt/` — Download PDF receipt

### Email Campaigns
- Managed via admin panel (Campaigns section)

---

## Staff Permissions
- Run:
  ```bash
  python manage.py create_staff_group
  ```
- Assign users to the "Staff" group in admin
- Staff can read/add/update products, orders, campaigns, but **cannot delete**

---

## PDF & Email
- **PDF Receipts/Reports**: WeasyPrint, downloadable from admin
- **Email Campaigns**: Visual/code editor, send to all users, template management

---

## Environment Variables
Add to `.env` or `settings.py`:
```python
STRIPE_PUBLISHABLE_KEY = 'pk_test_...'
STRIPE_SECRET_KEY = 'sk_test_...'
STRIPE_WEBHOOK_SECRET = 'whsec_...'
```

---

## Testing
```bash
python manage.py test
```

---

## Deployment
- Set `DEBUG = False`
- Use PostgreSQL for production
- Configure static/media file serving
- Set up Stripe keys and webhooks
- Use a production ASGI server (Daphne/Uvicorn)

---

## ASGI, Channels, and Real-Time Order Tracking

This project uses **Django Channels** and **Daphne** (ASGI server) for real-time features (WebSockets). Order status updates are pushed live to users via WebSocket.

- **ASGI Entrypoint:**
  - The app runs with Daphne (not Gunicorn) for full HTTP + WebSocket support.
  - Entrypoint: `backend.asgi:application`
- **Channels/Redis:**
  - Redis is used as the channel layer for production-ready real-time features.
  - All order status changes are broadcast to the user's WebSocket group.
- **Frontend Demo:**
  - See `public/order-tracker.html` for a simple order tracker using WebSockets.

### Running Locally (SQLite, no Docker)
1. Copy `.env.example` to `.env` and set `DJANGO_DB_ENGINE=sqlite` (default for local dev).
2. Run migrations, create a superuser, and start the server:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```
3. The app will use SQLite and run with Channels (ASGI) for real-time features.

### Running with Docker (Postgres + Redis, production-like)
1. Copy `.env.example` to `.env` and set `DJANGO_DB_ENGINE=postgresql`.
2. Build and start all services (app, Postgres, Redis):
   ```bash
   docker-compose up --build
   ```
3. The app will use Postgres and Redis, and run with **Daphne** for ASGI/Channels support (real-time features).
4. Access the app at `http://localhost:8000/` and the admin at `/admin/`.

### Using DevContainer (VS Code)
- Open the project in VS Code and reopen in container.
- All services (app, Postgres, Redis) are started automatically.
- Ports 8000 (app), 5432 (Postgres), and 6379 (Redis) are forwarded.
- Environment is loaded from `.devcontainer/devcontainer.env`.
- Migrations are run automatically on first start.

### CI/CD (GitHub Actions)
- On every push or pull request to `main`, the pipeline:
  - Spins up Postgres and Redis services
  - Installs dependencies
  - Runs migrations
  - Runs the full Django test suite
- See `.github/workflows/ci.yml` for details.

### Environment Variables
- Use `.env` for local/dev, `.env.example` as a template.
- Key variables:
  - `DJANGO_DB_ENGINE=sqlite` for local, `postgresql` for Docker/prod
  - `DEBUG=1` for local, `DEBUG=0` for production
  - `DJANGO_SECRET_KEY`, `DJANGO_DB_*`, `REDIS_HOST`, `REDIS_PORT`

### Testing ASGI/Channels
- Run the server and open `public/order-tracker.html` in your browser.
- Place an order, then update its status in the admin panel.
- You should see live status updates in the tracker page (WebSocket).

---

## License
MIT 