# CasettaFit Application

A comprehensive home gym weight lifting tracking application built with Flask.

## Quick Start (Development)

### 1. Install Dependencies

```bash
cd /opt/CasettaFit/app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
export FLASK_APP=run.py
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 3. Seed Admin User

```bash
cd /opt/CasettaFit
source app/venv/bin/activate
PYTHONPATH=/opt/CasettaFit python3 app/seed.py
```

### 4. Run Development Server

```bash
cd /opt/CasettaFit
source app/venv/bin/activate
PYTHONPATH=/opt/CasettaFit python3 app/run.py
```

The application will be available at `http://localhost:5000`

**Default Login:**
- Username: `admin`
- Password: `adminpass`

## Production Deployment

### Automated Setup (Ubuntu Server)

Run the setup script as root:

```bash
sudo bash /opt/CasettaFit/app/setup.sh
```

This will:
- Install system dependencies (Python, NGINX)
- Create virtual environment
- Install Python packages
- Initialize database
- Seed admin user
- Configure and start Gunicorn
- Configure and start NGINX

### Manual Setup

1. **Install system dependencies:**
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv nginx
```

2. **Set up Python environment:**
```bash
cd /opt/CasettaFit/app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Initialize database:**
```bash
export FLASK_APP=wsgi.py
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
python3 seed.py
```

4. **Configure Gunicorn:**
```bash
sudo cp casettafit.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable casettafit
sudo systemctl start casettafit
```

5. **Configure NGINX:**
```bash
sudo cp nginx.conf /etc/nginx/sites-available/casettafit
sudo ln -s /etc/nginx/sites-available/casettafit /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site
sudo nginx -t
sudo systemctl restart nginx
```

## Service Management

```bash
# View application logs
sudo journalctl -u casettafit -f

# Restart application
sudo systemctl restart casettafit

# Check status
sudo systemctl status casettafit

# Restart NGINX
sudo systemctl restart nginx
```

## Database Migrations

When making changes to models:

```bash
source venv/bin/activate
flask db migrate -m "Description of changes"
flask db upgrade
```

## Project Structure

```
app/
├── __init__.py          # Application factory
├── config.py            # Configuration
├── models.py            # Database models
├── forms.py             # WTForms
├── run.py               # Development server
├── wsgi.py              # Production WSGI entry point
├── seed.py              # Database seeding
├── requirements.txt     # Python dependencies
├── routes/              # Blueprint routes
│   ├── auth.py          # Authentication
│   ├── main.py          # Main pages
│   └── admin.py         # Admin pages
└── templates/           # Jinja2 templates
    ├── base.html
    ├── auth/
    ├── main/
    └── admin/
```

## Development

The application uses:
- **Flask** for the web framework
- **SQLite** for the database
- **Flask-Login** for authentication
- **Flask-Migrate** for database migrations
- **CoreUI** and **Bootstrap 5** for the frontend
- **Gunicorn** for production WSGI server
- **NGINX** for reverse proxy

## Security Notes

1. Change the default admin password immediately after first login
2. Set a strong `SECRET_KEY` environment variable in production
3. Use HTTPS in production (configure with Let's Encrypt)
4. Review and update NGINX security headers as needed

## Support

For issues or questions, contact the system administrator.
