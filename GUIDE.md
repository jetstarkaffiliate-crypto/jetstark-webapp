# Jetstark — Full Architecture & Deployment Guide

## Current State Analysis

### What Exists (`jetstark/` — 53 HTML/CSS/JS files)
- Static HTML pages with all business logic in a single 3071-line `script.js`
- All data stored in browser `localStorage` (5-10MB limit, no persistence)
- Passwords stored in **plaintext** in localStorage
- **XSS vulnerabilities** throughout (unsanitized `innerHTML` usage)
- No authentication (anyone can read/modify localStorage)
- No backend server, no database, no API
- No payment processing, no email service
- No rate limiting, no CSRF protection, no security headers

### Critical Issues Identified

| Severity | Issue | Location |
|----------|-------|----------|
| CRITICAL | Passwords stored in plaintext | `script.js:126` |
| CRITICAL | XSS via unsanitized innerHTML | ~50 locations across `script.js` |
| CRITICAL | No server-side authentication | Entire app |
| HIGH | All data in localStorage (no persistence) | Entire app |
| HIGH | No input validation server-side | Entire app |
| HIGH | No HTTPS/CORS/security headers | N/A |
| MEDIUM | 3071-line monolithic JS file | `script.js` |
| MEDIUM | Duplicate filter/render logic | Multiple `initialize*` functions |
| MEDIUM | Hardcoded sample data | `script.js:273-381` |
| LOW | No error boundaries | Throughout |

### Language Decision

**Switched from: Vanilla JS (frontend-only) → Python FastAPI (backend) + Vanilla JS (frontend)**

**Why Python/FastAPI:**
- **Type safety** via Pydantic — eliminates entire classes of bugs
- **Async by default** — handles 1000s of concurrent connections
- **Auto-generated OpenAPI docs** at `/api/docs`
- **SQLAlchemy ORM** — prevents SQL injection, handles migrations
- **Ecosystem** — best bcrypt/JWT/CORS libraries available
- **Paystack SDK** — first-class Python support for Nigerian payments

---

## New Architecture

```
jetstark/
├── backend/                        # Python FastAPI server
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry
│   │   ├── config.py               # Environment configuration
│   │   ├── database.py             # PostgreSQL async session
│   │   ├── api/                    # REST API routes
│   │   │   ├── auth.py             # JWT signup/login/refresh
│   │   │   ├── users.py            # Profile management
│   │   │   ├── products.py         # Product CRUD + admin moderation
│   │   │   ├── orders.py           # Order creation & history
│   │   │   ├── affiliates.py       # Link generation & analytics
│   │   │   ├── payouts.py          # Withdrawal requests
│   │   │   ├── reviews.py          # Product reviews
│   │   │   └── payments.py         # Paystack integration
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   ├── schemas/                # Pydantic validation schemas
│   │   ├── core/
│   │   │   ├── security.py         # bcrypt hashing, JWT tokens
│   │   │   └── dependencies.py     # Auth dependencies, role checks
│   │   └── services/
│   │       └── email.py            # Transactional email
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic.ini
├── frontend/                       # Modernized static frontend
│   ├── index.html                  # Landing page
│   ├── login.html                  # JWT-based login
│   ├── signup.html                 # Registration with validation
│   ├── css/styles.css              # Shared styles
│   └── js/
│       ├── api.js                  # API client with JWT refresh, sanitization
│       ├── auth.js                 # Auth functions
│       ├── marketplace.js          # Product/order functions
│       └── dashboard.js            # Dashboard/analytics functions
├── docker-compose.yml              # PostgreSQL + Redis + API + Nginx
├── nginx.conf                      # HTTPS, rate limiting, security headers
└── .gitignore
```

---

## Security Improvements

| Protection | Implementation |
|------------|---------------|
| **Password hashing** | bcrypt (12 rounds) via `passlib` |
| **JWT auth** | Access (30min) + Refresh (7d) tokens |
| **XSS prevention** | Server-side sanitization + `sanitizeHtml()` on all output |
| **SQL injection** | SQLAlchemy ORM (parameterized queries) |
| **CSRF** | Token-based auth (Bearer headers) |
| **Rate limiting** | Nginx: 30 req/s general, 5 req/s auth |
| **HTTPS** | Nginx redirect + Let's Encrypt cert |
| **Security headers** | HSTS, CSP, X-Frame-Options, X-Content-Type-Options |
| **CORS** | Whitelist-only origins |
| **Input validation** | Pydantic schemas on every endpoint |
| **Session management** | Server-side token validation, expiry |
| **Data encryption** | At-rest via PostgreSQL, in-transit via TLS |

---

## Step-by-Step: Prototype to Production

### Phase 1: Local Development Setup (Day 1)

```bash
# 1. Install dependencies
cd backend
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt

# 2. Copy & configure environment
cp .env.example .env
# Edit .env: set SECRET_KEY (generate: python -c "import secrets; print(secrets.token_hex(32))")

# 3. Start PostgreSQL (Docker)
cd ..
docker compose up -d db redis

# 4. Initialize database
cd backend
alembic init alembic
alembic revision --autogenerate -m "initial"
alembic upgrade head

# 5. Run development server
uvicorn app.main:app --reload --port 8000

# 6. Verify: http://localhost:8000/api/docs
```

### Phase 2: Core API Implementation (Days 2-5)

1. **Auth System** — Signup, login, token refresh, password change
2. **Products API** — CRUD, search, filter, sort, pagination
3. **Orders API** — Create orders, list history
4. **Affiliate API** — Link generation, click tracking, analytics
5. **Payouts API** — Balance queries, withdrawal requests
6. **Payments API** — Paystack initialize + verify

### Phase 3: Frontend Migration (Days 6-10)

1. Create `frontend/js/api.js` with JWT handling + sanitization
2. Create `frontend/js/auth.js` — signup/login/logout
3. Create `frontend/js/marketplace.js` — product browsing, cart
4. Create `frontend/js/dashboard.js` — affiliate stats, payouts
5. Update `frontend/login.html`, `frontend/signup.html` to use API
6. Copy existing CSS from `jetstark/styles.css` → `frontend/css/styles.css`

### Phase 4: Security Hardening (Days 11-13)

1. **Nginx rate limiting** — Already configured in `nginx.conf`
2. **CSP headers** — Already configured, test with browser
3. **Password policy** — Min 8 chars, bcrypt hashing
4. **Email verification** — Send welcome email via `services/email.py`
5. **2FA** — Implement TOTP via `pyotp` (future)
6. **Penetration testing** — Run OWASP ZAP against staging

### Phase 5: Payment Integration (Days 14-16)

1. Create Paystack merchant account
2. Set `PAYSTACK_SECRET_KEY` and `PAYSTACK_PUBLIC_KEY` in `.env`
3. Implement `POST /api/payments/initialize` in `payments.py`
4. Implement `GET /api/payments/verify/{reference}`
5. Test in Paystack test mode
6. Handle webhook callbacks for payment confirmation

### Phase 6: Email Service (Days 17-18)

1. Sign up for SendGrid/Mailgun
2. Set SMTP credentials in `.env`
3. Create welcome email template
4. Create payout notification template
5. Create password reset flow

### Phase 7: Deployment (Days 19-21)

```bash
# 1. Provision server (Ubuntu 22.04 on DigitalOcean/Vultr)
ssh root@your-server-ip

# 2. Install Docker + Compose
apt update && apt install -y docker.io docker-compose-plugin

# 3. Clone repo
git clone https://github.com/yourorg/jetstark.git /opt/jetstark
cd /opt/jetstark

# 4. Configure environment
cp backend/.env.example backend/.env
nano backend/.env    # Set production secrets

# 5. Start all services
docker compose up -d

# 6. Initial SSL certificate (first time)
docker compose run --rm certbot certonly --webroot \
  -w /usr/share/nginx/html -d jetstark.com -d www.jetstark.com

# 7. Restart Nginx to load SSL
docker compose restart nginx

# 8. Verify: https://jetstark.com/api/health
```

### Phase 8: Production Hardening (Days 22-25)

1. **Database backup** — Add daily pg_dump cron job
2. **Monitoring** — Set up Sentry error tracking
3. **Logging** — Configure structured logging with `structlog`
4. **CDN** — Put Cloudflare in front of Nginx
5. **CI/CD** — GitHub Actions for automated testing + deployment
6. **Load testing** — Use k6 to test 1000 concurrent users
7. **Disaster recovery** — Document restore procedures

### Phase 9: Remaining Work

| Feature | Priority | Status |
|---------|----------|--------|
| Vendor dashboard (product CRUD, stats) | HIGH | ✅ Done |
| Admin dashboard (approve/reject, user mgmt) | HIGH | ✅ Done |
| Paystack checkout flow | HIGH | ✅ Done |
| Affiliate click tracking + conversions | HIGH | ✅ Done |
| Auth-aware headers across all pages | HIGH | ✅ Done |
| Profile editing + password change | HIGH | ✅ Done |
| Deployment docs & docker-compose | HIGH | ✅ Done |
| README with full API reference | MEDIUM | ✅ Done |
| Buyer dashboard (digital downloads) | MEDIUM | Not started |
| Mobile app (React Native) | LOW | Not started |
| Real-time notifications (WebSocket) | LOW | Not started |
| CSV/PDF export | LOW | Not started |

---

## API Reference (Auto-Generated)

Once running, visit:
- **Swagger UI**: `https://jetstark.com/api/docs`
- **ReDoc**: `https://jetstark.com/api/redoc`

### Core Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/signup` | No | Create account |
| POST | `/api/auth/login` | No | Login, get JWT |
| POST | `/api/auth/refresh` | No | Refresh access token |
| GET | `/api/auth/me` | Yes | Current user profile |
| GET | `/api/products` | No | List published products |
| GET | `/api/products/{id}` | No | Product details |
| POST | `/api/products` | Vendor | Create product |
| POST | `/api/orders` | Yes | Place order |
| GET | `/api/orders` | Yes | Order history |
| POST | `/api/affiliate/links` | Affiliate | Generate link |
| GET | `/api/affiliate/analytics` | Affiliate | Get stats |
| POST | `/api/payouts` | Yes | Request payout |
| GET | `/api/payouts/balance` | Yes | Get balance |
| POST | `/api/payments/initialize` | Yes | Start payment |
| POST | `/api/reviews/products/{id}` | Yes | Submit review |

---

## Verification Checklist

- [ ] `https://jetstark.com/api/health` returns `{"status": "ok"}`
- [ ] Signup creates user, returns JWT tokens
- [ ] Login with correct credentials works
- [ ] Login with wrong password returns 401
- [ ] Accessing `/api/products` without auth returns products
- [ ] Creating a product without Vendor role returns 403
- [ ] Placing an order decrements inventory
- [ ] Affiliate link tracks clicks correctly
- [ ] Payout request creates pending payout
- [ ] Paystack payment initializes and verifies
- [ ] All endpoints have rate limiting (test with 50 req/s)
- [ ] HTTPS redirects from HTTP
- [ ] CSP headers present in response
- [ ] No XSS possible via product names/descriptions
- [ ] Lighthouse score > 90
