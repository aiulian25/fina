# FINA - Personal Finance Tracker

<div align="center">
  <img src="app/static/images/fina-logo.png" alt="FINA Logo" width="120" height="120">
  
  [![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
  [![Python](https://img.shields.io/badge/python-3.11-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
</div>

<img width="1917" height="928" alt="fina-welcome-page" src="https://github.com/user-attachments/assets/39be804d-6189-496f-81d0-d84dc4f2523f" />
<img width="1917" height="928" alt="fina-register-page" src="https://github.com/user-attachments/assets/e4944c80-964a-459e-aee5-dc2693e80646" />
<img width="1917" height="928" alt="fina-dashboard-new-setup" src="https://github.com/user-attachments/assets/c89edc8b-9e5d-4971-ab0f-7101b577d6dc" />
<img width="1917" height="928" alt="fina-dashboard-populated" src="https://github.com/user-attachments/assets/7e181b63-1c55-4d12-a03b-30606cb4d03f" />
<img width="1917" height="928" alt="fina-create-category" src="https://github.com/user-attachments/assets/3885a4f0-2e35-41ca-b2a5-0ae62a76cee1" />
<img width="1917" height="928" alt="fina-expense-entry" src="https://github.com/user-attachments/assets/d5085626-6cbd-48d3-a4ae-3a0f1f31af19" />
<img width="1917" height="928" alt="fina-settings-page" src="https://github.com/user-attachments/assets/b38d53ab-8aa9-4c36-b040-e6ab5331f9ba" />
<img width="1917" height="928" alt="fina-settings-page-2FA" src="https://github.com/user-attachments/assets/c6ccc285-8191-4a70-ac3b-bd60ed72dae5" />
<img width="1917" height="928" alt="fina-tags-page" src="https://github.com/user-attachments/assets/75af122d-7bc6-4e0b-a57b-729fe75a48b6" />


Disclaimer

USE AT YOUR OWN RISK: This software is provided "as is", without warranty of any kind, express or implied. By using FINA, you acknowledge that you understand and accept these risks.
 About

FINA is a modern, self-hosted personal finance tracker built with Flask and Docker. Track expenses, manage categories, visualize spending patterns, and keep your financial data completely under your control.
 Features

     Expense tracking with custom categories

     Interactive pie and bar charts

     Tag management system

     Receipt uploads (images/PDFs)

     Two-factor authentication

     Multi-user support

     Multi-currency (USD, EUR, GBP, RON)

     CSV import/export

     Modern glassmorphism UI

     Mobile responsive

 Quick Start
Prerequisites

    Docker and Docker Compose installed

    Port 5001 available

Installation

1. Create project directory:

mkdir fina
cd fina

2. Create docker-compose.yml:


version: '3.8'

services:
  web:
    image: aiulian25/fina:latest
    container_name: fina-web
    ports:
      - "5001:5000"
    volumes:
      - fina-db:/app/instance
      - fina-uploads:/app/app/static/uploads
    environment:
      - FLASK_APP=wsgi.py
      - FLASK_ENV=production
      - REDIS_HOST=redis
      - REDIS_PORT=6369
      - SECRET_KEY=${SECRET_KEY:-change-this-secret-key-in-production}
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:alpine
    container_name: fina-redis
    ports:
      - "6369:6379"
    restart: unless-stopped

volumes:
  fina-db:
  fina-uploads:

3. (Optional but recommended) Create .env file:

Create a file called .env with your custom secret key:

text
SECRET_KEY=your-super-secret-random-key-here

To generate a secure random key:

bash
openssl rand -hex 32

4. Start FINA:

bash
docker compose up -d

5. Access FINA:

Open your browser to: http://localhost:5001

    Register your first user (automatically becomes admin)

    Start tracking your expenses!

 Configuration
Environment Variables
Variable	Default	Description
SECRET_KEY	change-this-secret-key-in-production	Flask secret key for sessions
REDIS_HOST	redis	Redis hostname
REDIS_PORT	6369	Redis port
Ports

    5001: Web application (customizable in docker-compose.yml)

    6369: Redis cache

 Usage
First Time Setup

    Register your account - first user becomes admin

    Go to Settings → Profile to set your currency

    (Optional) Enable 2FA in Settings → Security

    Create expense categories

    Start adding expenses!

Admin Features

Access Settings → User Management to:

    Create managed user accounts

    Edit user details and roles

    Delete users

Data Management

    Export: Settings → Import/Export → Export to CSV

    Import: Settings → Import/Export → Upload CSV

    Backups: Data stored in Docker volumes fina-db and fina-uploads

 Security

IMPORTANT for production deployments:

     Change the SECRET_KEY in .env file

     Use HTTPS with a reverse proxy (nginx, Caddy, Traefik)

     Enable 2FA for all users

     Regular database backups

     Keep Docker images updated

     Restrict network access

Reverse Proxy Example (Caddy)

text
fina.yourdomain.com {
    reverse_proxy localhost:5001
}

 Docker Commands

bash
# Start FINA
docker compose up -d

# Stop FINA
docker compose down

# View logs
docker compose logs -f web

# Restart
docker compose restart

# Update to latest version
docker compose pull
docker compose up -d

# Check status
docker compose ps

 Building from Source

If you prefer to build from source instead of using the pre-built image:

bash
git clone https://github.com/aiulian25/fina.git
cd fina
docker compose -f docker-compose.build.yml up -d --build

 Contributing

Contributions are welcome! Please:

    Fork the repository

    Create your feature branch (git checkout -b feature/AmazingFeature)

    Commit your changes (git commit -m 'Add AmazingFeature')

    Push to the branch (git push origin feature/AmazingFeature)

    Open a Pull Request

 License

This project is licensed under the MIT License - see the LICENSE file for details.
 Support

For issues or questions:

    Open an issue on GitHub

    Check existing documentation

 Acknowledgments

Built using:

    Flask & Python

    Docker & Docker Compose

    Chart.js for visualizations

    Redis for caching

Remember: Always back up your data and secure your deployment. This software handles sensitive financial information.

