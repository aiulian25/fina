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



## Disclaimer

**USE AT YOUR OWN RISK**: This software is provided "as is", without warranty of any kind, express or implied. The authors and contributors assume no responsibility for any damages, data loss, security breaches, or other issues that may arise from using this software. Users are solely responsible for:

- Securing their deployment
- Backing up their data
- Configuring appropriate security measures
- Complying with applicable data protection regulations

By using FINA, you acknowledge that you understand and accept these risks.

---

##  About

FINA is a modern, self-hosted personal finance tracker built with Flask and Docker. Track your expenses, manage categories, visualize spending patterns, and keep your financial data completely under your control.

###  Features

- ** Expense Tracking**: Organize expenses by custom categories
- ** Visual Analytics**: Interactive pie and bar charts for spending insights
- ** Tagging System**: Tag expenses for better organization
- ** Receipt Management**: Upload and store receipt images/PDFs
- ** Two-Factor Authentication**: Optional 2FA for enhanced security
- ** Multi-User Support**: Admin can create and manage user accounts
- ** Multi-Currency**: Support for USD, EUR, GBP, and RON
- ** Import/Export**: CSV import and export functionality
- ** Modern UI**: Beautiful dark-themed glassmorphism design
- ** Mobile Responsive**: Works seamlessly on all devices

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Ports 5001 and 6369 available on your host

### Installation

1. **Clone the repository:**
git clone https://github.com/aiulian25/fina.git
docker compose up -d

## Configuration

### Environment Variables

Create a `.env` file to customize your deployment:

SECRET_KEY=your-super-secret-key-change-this
REDIS_HOST=redis
REDIS_PORT=6369

**Access FINA:**
- Open your browser to `http://localhost:5001`
- Register your first user (automatically becomes admin)
- Start tracking!

### Ports

- **5001**: Web application (can be changed in docker-compose.yml)
- **6369**: Redis cache

### Pull 
Docker Compose Recomended

- mkdir fina
- cd fina
- nano docker-compose.yml

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
      - SECRET_KEY=${SECRET_KEY:-change-this-secret-key-openssl rand -hex 32}
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

### (Optional but recommended): Create .env file:

SECRET_KEY=ozZp4DTXGoFHZ2zFHis0oBWaYJ5jpw4x
DATABASE_URL=sqlite:///finance.db
REDIS_URL=redis://redis:6369/0
FLASK_ENV=production



## Usage

### First Time Setup

1. Register your account - first user becomes admin
2. Go to Settings → Profile to set your currency
3. (Optional) Enable 2FA in Settings → Security
4. Create expense categories
5. Start adding expenses!

### Admin Features

Admins can access User Management in Settings to:
- Create managed user accounts
- Edit user details and roles
- Manage system users

### Data Management

- **Export**: Settings → Import/Export → Export to CSV
- **Import**: Settings → Import/Export → Upload CSV file
- **Backups**: Data persists in Docker volumes `fina-db` and `fina-uploads`

## Security Considerations

**IMPORTANT**: This application is designed for self-hosting. Please consider:

1. **Change the default SECRET_KEY** in production
2. **Use HTTPS** with a reverse proxy (nginx, Caddy, Traefik)
3. **Enable 2FA** for all users
4. **Regular backups** of your data
5. **Keep Docker images updated**
6. **Restrict network access** to trusted devices only

### Recommended Production Setup

Start

docker compose up -d
Stop

docker compose down
View logs

docker compose logs -f web
Restart

docker compose restart
Update to latest

docker compose pull
docker compose up -d


## Tech Stack

- **Backend**: Python 3.11, Flask, SQLAlchemy
- **Database**: SQLite
- **Cache**: Redis
- **Frontend**: Vanilla JavaScript, Chart.js
- **Security**: Flask-Login, Flask-WTF (CSRF), pyotp (2FA)
- **Deployment**: Docker, Gunicorn

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with using Flask and modern web technologies
- Icons and design inspiration from various open-source projects

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation

---

**Remember**: Always back up your data and secure your deployment appropriately. This software handles sensitive financial information.
