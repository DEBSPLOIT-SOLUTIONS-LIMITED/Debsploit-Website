# Debsploit Solutions - Django REST API

A comprehensive Django REST API system with custom admin UI, MySQL database, and comprehensive documentation.

## 🚀 Features

- **REST API**: Full-featured API with Django REST Framework
- **Custom Admin UI**: Bootstrap-based admin dashboard
- **MySQL Database**: Production-ready database configuration
- **JWT Authentication**: Secure token-based authentication
- **API Documentation**: Swagger UI and ReDoc integration
- **User Management**: Custom user model with profiles
- **Services Management**: Service categories, services, and reviews
- **Blog System**: Content management with categories
- **File Uploads**: Image handling with Pillow
- **Email Integration**: Django Allauth with social authentication

## 📋 Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Admin Interface](#admin-interface)
- [Authentication](#authentication)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## 🛠 Installation

### Prerequisites

- Python 3.8+
- MySQL 8.0+
- pip (Python package manager)

### 1. Clone the Repository

```bash
git clone https://github.com/DEBSPLOIT-SOLUTIONS-LIMITED/Debsploit-Website.git
cd debsploit_solutions
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

### 1. Environment Variables

Create a `.env` file in the root directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here-change-this-in-production
DEBUG=True

# Database Configuration
DB_NAME=debsploit_solutions
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
EMAIL_USE_TLS=True

# Social Authentication (Optional)
GOOGLE_OAUTH2_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH2_CLIENT_SECRET=your_google_client_secret

# Site Configuration
SITE_URL=http://localhost:8000
DEFAULT_FROM_EMAIL=noreply@debsploitsolutions.com

# Security (Production)
SECURE_HSTS_SECONDS=31536000
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 2. MySQL Database Setup

```sql
-- Create database
CREATE DATABASE debsploit_solutions CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user (optional)
CREATE USER 'debsploit_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON debsploit_solutions.* TO 'debsploit_user'@'localhost';
FLUSH PRIVILEGES;
```

## 🗄️ Database Setup

### 1. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Create Superuser

```bash
python manage.py create_admin
```

Follow the prompts to create an admin account with:
- Email address
- First name
- Last name  
- Password

### 3. Load Sample Data (Optional)

```bash
python manage.py loaddata fixtures/sample_data.json
```

## 🚀 Running the Application

### Development Server

```bash
python manage.py runserver
```

The application will be available at:
- **Admin UI**: http://localhost:8000/
- **Django Admin**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/api/docs/

### Production Deployment

```bash
# Collect static files
python manage.py collectstatic --noinput

# Run with Gunicorn
gunicorn debsploit_solutions.wsgi:application --bind 0.0.0.0:8000
```

## 📡 API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration
- `POST /api/auth/refresh/` - Refresh JWT token
- `POST /api/auth/logout/` - User logout

### Users
- `GET /api/users/` - List users
- `GET /api/users/{id}/` - Get user details
- `PUT /api/users/{id}/` - Update user
- `DELETE /api/users/{id}/` - Delete user

### Services
- `GET /api/services/categories/` - List service categories
- `POST /api/services/categories/` - Create category
- `GET /api/services/services/` - List services
- `POST /api/services/services/` - Create service
- `GET /api/services/reviews/` - List reviews
- `POST /api/services/reviews/` - Create review

### Blog
- `GET /api/blog/posts/` - List blog posts
- `POST /api/blog/posts/` - Create blog post
- `GET /api/blog/categories/` - List blog categories
- `POST /api/blog/categories/` - Create blog category

### API Documentation
- `GET /swagger/` - Swagger UI
- `GET /api/docs/` - ReDoc documentation
- `GET /api/schema/` - OpenAPI schema

## 🎛️ Admin Interface

### Custom Admin Dashboard

Access the custom admin interface at `http://localhost:8000/`

Features:
- **Dashboard**: Overview with statistics
- **User Management**: Create, edit, delete users
- **Services Management**: Manage categories, services, reviews
- **Blog Management**: Manage posts and categories
- **Settings**: System configuration

### Django Admin

Access Django's built-in admin at `http://localhost:8000/admin/`

## 🔐 Authentication

### JWT Authentication

The API uses JWT (JSON Web Tokens) for authentication:

1. **Login**: POST to `/api/auth/login/` with email and password
2. **Get Tokens**: Receive access and refresh tokens
3. **Use Token**: Include in Authorization header: `Bearer <access_token>`
4. **Refresh**: Use refresh token to get new access token

### Example Authentication Flow

```python
import requests

# Login
response = requests.post('http://localhost:8000/api/auth/login/', {
    'email': 'user@example.com',
    'password': 'your_password'
})

tokens = response.json()
access_token = tokens['access']

# Use token in subsequent requests
headers = {'Authorization': f'Bearer {access_token}'}
response = requests.get('http://localhost:8000/api/users/', headers=headers)
```

## 🌍 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Required |
| `DEBUG` | Debug mode | `True` |
| `DB_NAME` | Database name | `debsploit_solutions` |
| `DB_USER` | Database user | `root` |
| `DB_PASSWORD` | Database password | Required |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `3306` |
| `EMAIL_HOST` | SMTP host | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_HOST_USER` | SMTP username | Required |
| `EMAIL_HOST_PASSWORD` | SMTP password | Required |

## 📁 Project Structure

```
debsploit_solutions/
├── accounts/                 # User management app
│   ├── migrations/
│   ├── management/
│   │   └── commands/
│   │       └── create_admin.py
│   ├── models.py            # Custom User model
│   ├── serializers.py       # API serializers
│   ├── api_views.py         # API views
│   └── urls.py              # URL patterns
├── admin_ui/                # Custom admin interface
│   ├── templates/
│   │   └── admin_ui/
│   │       ├── base.html
│   │       ├── dashboard.html
│   │       ├── users.html
│   │       ├── services.html
│   │       ├── blog.html
│   │       └── settings.html
│   ├── views.py             # Admin views
│   └── urls.py
├── blog/                    # Blog management app
│   ├── migrations/
│   ├── models.py            # Blog models
│   ├── serializers.py       # API serializers
│   ├── api_views.py         # API views
│   └── urls.py
├── services/                # Services management app
│   ├── migrations/
│   ├── models.py            # Service models
│   ├── serializers.py       # API serializers
│   ├── api_views.py         # API views
│   └── urls.py
├── core/                    # Core functionality
├── dashboard/               # Dashboard utilities
├── debsploit_solutions/     # Main project settings
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URL configuration
│   └── wsgi.py
├── static/                  # Static files (CSS, JS)
│   ├── css/
│   └── js/
├── media/                   # User uploaded files
├── logs/                    # Application logs
├── requirements.txt         # Python dependencies
├── manage.py               # Django management script
└── README.md               # This file
```

## 🛠️ Development

### Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Write unit tests for new features

### Database Migrations

```bash
# Create migrations for model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

### Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Debug Commands

```bash
# Check for issues
python manage.py check

# Open Django shell
python manage.py shell

# Create database backup
python manage.py dbbackup

# Load database backup
python manage.py dbrestore
```

## 🔧 API Usage Examples

### User Registration

```python
import requests

data = {
    'email': 'newuser@example.com',
    'first_name': 'John',
    'last_name': 'Doe',
    'password': 'securepassword123',
    'password_confirm': 'securepassword123'
}

response = requests.post('http://localhost:8000/api/auth/register/', json=data)
print(response.json())
```

### Create Service

```python
import requests

# First, get authentication token
auth_response = requests.post('http://localhost:8000/api/auth/login/', {
    'email': 'admin@example.com',
    'password': 'adminpassword'
})
token = auth_response.json()['access']

# Create service
headers = {'Authorization': f'Bearer {token}'}
service_data = {
    'name': 'Web Development',
    'description': 'Professional web development services',
    'price': 999.99,
    'category': 1
}

response = requests.post('http://localhost:8000/api/services/services/', 
                        json=service_data, headers=headers)
print(response.json())
```

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "debsploit_solutions.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### Environment Setup

1. **Development**: Use SQLite, DEBUG=True
2. **Staging**: Use MySQL, DEBUG=True, limited access
3. **Production**: Use MySQL, DEBUG=False, secure settings

## 📊 Monitoring

### Health Check Endpoint

```bash
curl http://localhost:8000/api/health/
```

### Logging

Logs are stored in `logs/django.log` and include:
- Request/Response logs
- Error logs
- Security logs
- Performance metrics

## 🔒 Security

### Security Features

- CSRF protection enabled
- SQL injection protection
- XSS protection
- Secure password hashing
- JWT token expiration
- Rate limiting (optional)

### Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Set DEBUG=False in production
- [ ] Use HTTPS in production
- [ ] Configure proper CORS settings
- [ ] Set up proper backup strategy
- [ ] Monitor security logs

## 📈 Performance

### Optimization Tips

1. **Database**: Use indexes, optimize queries
2. **Caching**: Implement Redis caching
3. **Static Files**: Use CDN for static files
4. **Images**: Optimize image sizes
5. **Monitoring**: Set up application monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/Debsploit-Website.git

# Set up development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up pre-commit hooks
pre-commit install
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, email support@debsploitsolutions.com or create an issue on GitHub.

## 🙏 Acknowledgments

- Django REST Framework team
- Bootstrap team
- All contributors and testers

---

**Debsploit Solutions** - Building the future of cybersecurity education and services.
