# FINA - Personal Finance Tracker

A modern, secure PWA for tracking expenses with multi-user support, visual analytics, and comprehensive financial management.

![Dashboard](docs/screenshots/dashboard.png)

## ✨ Features

- 💰 **Expense Tracking** - Custom categories, tags, and receipt attachments
- 📊 **Analytics Dashboard** - Interactive charts and spending insights
- 🔄 **Recurring Transactions** - Automatic tracking of subscriptions and bills
- 🎯 **Budget Goals** - Set and track monthly spending limits
- 📈 **Income Management** - Track multiple income sources
- 🔐 **Secure Authentication** - With optional 2-Factor Authentication
- 👥 **Multi-User Support** - Role-based access control
- 🌍 **Multi-Language** - English, Romanian
- 💱 **Multi-Currency** - USD, EUR, GBP, RON
- 📱 **Progressive Web App** - Install on any device
- 🎨 **Modern UI** - Glassmorphism design with dark/light themes
- 📤 **CSV Import/Export** - Easy data migration
- 🧾 **Receipt OCR** - Extract data from receipts automatically

## 📸 Screenshots

<details>
<summary>Click to view screenshots</summary>

| Dashboard | Transactions | Analytics |
|-----------|--------------|-----------|
| ![Dashboard](docs/screenshots/dashboard.png) | ![Transactions](docs/screenshots/transactions.png) | ![Analytics](docs/screenshots/analytics.png) |

| Goals | Income | Settings |
|-------|--------|----------|
| ![Goals](docs/screenshots/goals.png) | ![Income](docs/screenshots/income.png) | ![Settings](docs/screenshots/settings.png) |

</details>

---

## 🚀 Quick Start (Production)

### Prerequisites

- Docker & Docker Compose
- GitHub account (for pulling from ghcr.io)

### 1. Login to GitHub Container Registry

```bash
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u YOUR_USERNAME --password-stdin
```

> Create a token at: GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic) → Generate new token with `read:packages` scope

### 2. Clone the repo (or download files)

```bash
git clone https://github.com/aiulian25/fina.git
cd fina
```

Or for minimal deployment (just the compose file):
```bash
mkdir fina && cd fina
# Copy docker-compose.prod.yml and .env.example from the repo
```

### 3. Configure environment

```bash
# Copy template and edit
cp .env.example .env
nano .env
```

**Important:** Change `SECRET_KEY` to a secure random string:
```bash
# Generate a secure key
openssl rand -hex 32
```

### 4. Pull and run

```bash
docker compose pull
docker compose up -d
```

### 5. Access the app

```
http://YOUR_SERVER_IP:5103
```

---

## ⚙️ Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | `change_this_in_production` |
| `HTTPS_ENABLED` | Set `true` if behind HTTPS proxy | `false` |
| `SESSION_LIFETIME` | Session duration in seconds | `604800` (7 days) |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `DATABASE_URL` | Database path | `sqlite:////app/data/fina.db` |

---

## 🔄 Update to Latest Version

```bash
docker compose pull
docker compose up -d
```

---

## 📋 Useful Commands

```bash
# View logs
docker compose logs -f

# Stop the app
docker compose down

# Restart
docker compose restart

# Check status
docker compose ps
```

---

## 🛠️ Development Setup

For local development with hot-reload:

```bash
git clone https://github.com/aiulian25/fina.git
cd fina
docker compose up -d
```

Access at `http://localhost:5103`

---

## 🏗️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Flask 3.0 (Python 3.11) |
| Database | SQLite |
| Cache/Sessions | Redis |
| Frontend | Tailwind CSS, Chart.js |
| Containerization | Docker |

---

## 🔒 Security Features

- Password hashing with bcrypt (12 rounds)
- CSRF protection on all forms
- Rate limiting on authentication endpoints
- Secure session management with Redis
- Content Security Policy headers
- Optional 2FA with TOTP

---

## 📝 License

MIT

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
