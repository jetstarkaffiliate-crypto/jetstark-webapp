# Jetstark Affiliate Hub

A secure, production-grade digital products marketplace with affiliate marketing. Built with FastAPI + PostgreSQL + Vanilla JS.

## Quick Start

```powershell
# Prerequisites: Docker Desktop, Python 3.14+, Node.js (optional)

# 1. Start database containers
docker compose up -d db redis

# 2. Create venv and install dependencies
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Run database setup
$env:PYTHONPATH = "."
python -c "import asyncio; from app.database import init_db; asyncio.run(init_db())"
python seed.py

# 4. Start API (separate terminal)
cd backend
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Start frontend (separate terminal)
cd frontend
python -m http.server 5500

# 6. Open http://localhost:5500
```

Or use the one-click script: `.\start.ps1`

## Architecture

```
jetstark/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/          # Route handlers (auth, users, products, orders, etc.)
│   │   ├── core/         # Security (bcrypt, JWT), dependencies
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── main.py       # FastAPI app entry point
│   │   ├── config.py     # Settings from .env
│   │   ├── database.py   # Async SQLAlchemy engine
│   │   └── seed.py       # Database seeder
│   ├── alembic/          # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/             # Static HTML/CSS/JS
│   ├── index.html        # Landing page
│   ├── marketplace.html  # Product listing
│   ├── product-detail.html
│   ├── checkout.html
│   ├── login.html / signup.html
│   ├── dashboard.html    # Role-based router
│   ├── account.html      # Profile editing
│   ├── orders.html
│   ├── vendor-dashboard.html  # Product CRUD
│   ├── admin-dashboard.html   # Approve/reject, user mgmt
│   ├── affiliate-dashboard.html
│   ├── affiliate-links.html
│   ├── affiliate-payouts.html
│   ├── how-it-works.html
│   ├── css/styles.css
│   └── js/
│       ├── api.js         # API client (JWT auth, XSS sanitization)
│       ├── auth.js        # Signup, login, logout, header
│       ├── marketplace.js # Product grid, cart, checkout
│       └── dashboard.js   # Affiliate analytics, links, payouts
├── docker-compose.yml     # PostgreSQL 16 + Redis 7 + API + Nginx
├── nginx.prod.conf        # Production HTTPS config
├── nginx.dev.conf         # Local dev config
├── start.ps1 / stop.ps1   # One-click dev scripts
└── README.md
```

## Features

- **Role-based access control** — Admin, Vendor, Affiliate, Buyer
- **Vendor dashboard** — Create/edit/delete products, sales stats
- **Admin panel** — Product approval workflow, user management, order overview
- **Affiliate system** — Link generation, click tracking, conversion tracking, analytics, payouts
- **Paystack payments** — Nigerian naira (NGN) payments with inline.js popup
- **Secure** — bcrypt(12), JWT access/refresh tokens, CSP headers, rate limiting, XSS sanitization
- **Async** — FastAPI + asyncpg for high concurrency

## API Endpoints

### Public
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/config` | Public config (Paystack key) |
| POST | `/api/auth/signup` | Register |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/refresh` | Refresh token |
| GET | `/api/products` | List published products |
| GET | `/api/products/{id}` | Product detail |

### Authenticated
| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/api/auth/me` | Any | Current user |
| PUT | `/api/auth/change-password` | Any | Change password |
| PUT | `/api/users/profile` | Any | Update profile |
| POST | `/api/orders` | Any | Create order |
| GET | `/api/orders` | Any | My orders |
| POST | `/api/reviews/products/{id}` | Any | Submit review |

### Vendor
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/products/my-products` | My products |
| POST | `/api/products` | Create product |
| PUT | `/api/products/{id}` | Update product |
| DELETE | `/api/products/{id}` | Delete product |

### Affiliate
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/affiliate/analytics` | Dashboard stats |
| POST | `/api/affiliate/links` | Create link |
| GET | `/api/affiliate/links` | My links |
| DELETE | `/api/affiliate/links/{id}` | Delete link |
| POST | `/api/affiliate/track-click` | Track click |
| POST | `/api/payouts` | Request payout |
| GET | `/api/payouts` | Payout history |
| GET | `/api/payouts/balance` | Balance |

### Admin
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/products/admin/pending` | Pending products |
| GET | `/api/products/admin/all` | All products |
| POST | `/api/products/admin/{id}/approve` | Approve product |
| POST | `/api/products/admin/{id}/reject` | Reject product |
| GET | `/api/users/admin/users` | List users |
| POST | `/api/users/admin/users/{id}/suspend` | Suspend user |
| GET | `/api/orders/admin/all` | All orders |

### Payments
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/payments/initialize` | Initialize Paystack |
| POST | `/api/payments/verify/{ref}` | Verify payment |

## Test Accounts

After running `seed.py`:

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@jetstark.com | Admin123! |
| Vendor | vendor@jetstark.com | Vendor123! |
| Affiliate | affiliate@jetstark.com | Affiliate123! |
| Buyer | buyer@jetstark.com | Buyer123! |

## Deployment

```bash
# Production (with SSL)
docker compose --profile prod up -d

# Initial SSL cert (replace domain)
docker compose run --rm certbot certonly --webroot -w /usr/share/nginx/html -d jetstark.com
```

Requires `backend/.env` configured with:
- `SECRET_KEY` — 64-char random string
- `PAYSTACK_SECRET_KEY` — Paystack live key
- `PAYSTACK_PUBLIC_KEY` — Paystack public key
- `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` — Email credentials (optional)
- `SENTRY_DSN` — Error tracking (optional)
