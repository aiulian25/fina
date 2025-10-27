cat > README.md << 'EOF'
# FINA - Personal Finance Tracker

<div align="center">
  <img src="app/static/images/fina-logo.png" alt="FINA Logo" width="120" height="120">
  
  [![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
  [![Python](https://img.shields.io/badge/python-3.11-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
</div>

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

## 📖 Usage

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
# fina
