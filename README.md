# 🔐 Secure Transaction Management System (TMS)

A production-grade financial transaction manager with **End-to-End AES-256 Encryption**, **JWT Authentication**, and **Role-Based Access Control** — available as both a **PyQt6 Desktop Application** and a **React Web Application**.

---

## 🏗️ Architecture

```
TMS/
├── backend/          → FastAPI (Python) — REST API, encryption, auth
├── desktop/          → PyQt6 Desktop Application  
├── web/              → React + Vite Web Application
├── docker-compose.yml
└── .env.example
```

**3-Tier:** React/PyQt6 → FastAPI → PostgreSQL (Supabase)

---

## 🔒 Security Features

| Feature | Implementation |
|---------|----------------|
| Field Encryption | AES-256-GCM (Fernet) via `cryptography` library |
| Password Hashing | bcrypt via `passlib` |
| Session Auth | JWT Access (30 min) + Refresh (7 days) tokens |
| Authorization | Role-Based Access Control (Admin / User) |
| Transport | HTTPS via Nginx, CORS headers |
| Rate Limiting | SlowAPI — 60 requests/min per IP |
| Audit Logs | Every write action logged with IP + user |

**Encrypted fields:** Customer name, mobile number, customer ID, account numbers, beneficiary details, transaction notes.

---

## ⚡ Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL or Supabase account

### 1. Clone & Configure

```bash
cd TMS
cp .env.example .env
# Edit .env with your database URL and generate keys (see below)
```

### 2. Generate Encryption Key

```bash
cd backend
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Paste output as AES_ENCRYPTION_KEY in .env
```

### 3. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

> API docs available at: **http://localhost:8000/docs**  
> Default admin: `admin` / `Admin@123!` (set in `.env`)

### 4. Web Frontend Setup

```bash
cd web
npm install
npm run dev
```

> Web app at: **http://localhost:5173**

### 5. Desktop Application

```bash
cd desktop
python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
python main.py
```

> Configure backend URL via `TMS_API_URL` env var (default: `http://localhost:8000`)

---

## 🐳 Docker Deployment

```bash
# Configure .env first
cp .env.example .env
# Edit .env with production values

# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f backend
```

Services:
- **Backend**: http://localhost:8000
- **Web UI**: http://localhost:80
- **PostgreSQL**: localhost:5432 (local dev only)

---

## ☁️ Supabase Setup (Recommended Cloud DB)

1. Create a project at [supabase.com](https://supabase.com)
2. Go to **Settings → Database** → copy the **Connection string (URI)**
3. Set in `.env`:
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres
   ```

---

## 📊 Dashboard Features

- **Summary Cards**: Total transactions, withdrawals, transfers, today's amount, monthly amount
- **Daily Line Chart**: Transaction amounts over the last 30 days
- **App Usage Pie Chart**: PhonePe, Paytm, PayNear, Bank App, ATM, UPI breakdown
- **Bank-wise Bar Chart**: Transaction amounts per bank
- **Monthly Trend**: Monthly spending over time

---

## 👤 Default Roles

| Role | Capabilities |
|------|-------------|
| **Admin** | Full access: manage users, view audit logs, all CRUD |
| **User** | Add/view/delete own transactions, banks, beneficiaries; export reports |

---

## 🔑 Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `AES_ENCRYPTION_KEY` | Fernet key for AES-256 field encryption |
| `SECRET_KEY` | JWT signing secret (generate with `secrets.token_urlsafe(32)`) |
| `ADMIN_USERNAME` | Default admin username |
| `ADMIN_PASSWORD` | Default admin password |

---

## 📦 Export Formats

- **CSV** — via `csv` module
- **Excel (.xlsx)** — via `openpyxl` (styled headers, alternating rows)
- **PDF** — via `reportlab` (landscape A4, colored header row)

---

## 🧪 Running Tests

```bash
cd backend
pip install pytest pytest-asyncio httpx
pytest tests/ -v --tb=short
```

Tests cover: AES-256 round-trip, JWT encode/decode, auth endpoints, RBAC.

---

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login → JWT tokens |
| POST | `/api/auth/register` | Create user |
| POST | `/api/auth/refresh` | Refresh access token |
| GET/POST | `/api/transactions` | List / create transactions |
| GET/POST | `/api/banks` | List / create banks |
| GET/POST | `/api/beneficiaries` | List / create beneficiaries |
| GET | `/api/dashboard/summary` | Summary card data |
| GET | `/api/dashboard/daily-chart` | Line chart data |
| GET | `/api/dashboard/app-usage` | Pie chart data |
| GET | `/api/dashboard/bank-wise` | Bar chart data |
| GET | `/api/reports/export/csv` | Export CSV |
| GET | `/api/reports/export/excel` | Export Excel |
| GET | `/api/reports/export/pdf` | Export PDF |
| GET | `/api/audit` | Audit logs (Admin only) |
| GET/PUT/DELETE | `/api/users/{id}` | User management (Admin only) |

---

## 🔧 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.0 async |
| **Database** | PostgreSQL (Supabase) / SQLite (dev) |
| **Encryption** | `cryptography` (AES-256-GCM + Fernet) |
| **Auth** | `python-jose` (JWT), `passlib` (bcrypt) |
| **Desktop** | PyQt6, Matplotlib |
| **Web** | React 18, Vite, Recharts, Axios |
| **Deployment** | Docker, Docker Compose, Nginx |
| **Reports** | openpyxl (Excel), reportlab (PDF) |

---

## 📁 Transaction Apps Supported

PhonePe · Paytm · PayNear · Bank App · ATM · UPI · Cash · Other
