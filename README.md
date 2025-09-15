# Wedding Planner - Flask Application

A modern wedding RSVP management system built with Flask, featuring an admin dashboard and guest management.

##  Quick Deploy to Coolify

### Prerequisites
- Coolify instance running
- Domain configured (e.g., james-and-heather.com)
- Cloudflare account for tunnel setup

### Deployment Steps

1. **Connect Repository to Coolify**
   - In Coolify dashboard, create new project
   - Connect your Git repository
   - Select this repository

2. **Configure Environment**
   - **Domain**: james-and-heather.com
   - **Build Command**: pip install -r requirements.txt
   - **Start Command**: python app.py
   - **Port**: 5000
   - **Health Check**: / (enabled)

3. **Environment Variables**
   Configure these in Coolify environment settings:
   `
   SECRET_KEY=your-random-secret-key-here
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your-secure-admin-password
   DATABASE_URL=sqlite:///wedding.db
   `

4. **Deploy**
   - Coolify will automatically build and deploy
   - The app will be available at your configured domain

##  Cloudflare Tunnel Setup

### Option 1: Coolify Built-in Tunnel (Recommended)
1. In Coolify project settings
2. Enable "Cloudflare Tunnel"
3. Add your domain (e.g., james-and-heather.com)
4. Coolify handles the tunnel automatically

### Option 2: Manual Cloudflare Tunnel
If you prefer manual setup:

`ash
# Install cloudflared
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Login to Cloudflare
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create wedding-planner

# Create DNS record
cloudflared tunnel route dns wedding-planner james-and-heather.com

# Run tunnel
cloudflared tunnel run wedding-planner
`

##  Project Structure

`
 app.py                 # Main Flask application
 requirements.txt       # Python dependencies
 Dockerfile            # Docker container configuration
 docker-compose.yml    # Docker compose for local development
 models.py             # Database models
 blueprints/           # Flask blueprints
    public/          # Public website routes
    admin/           # Admin dashboard routes
    api/             # API endpoints
 static/              # Static assets (CSS, JS)
 templates/           # Jinja2 templates
    base.html        # Base template
    index.html       # Main wedding page
    rsvp.html        # RSVP form
    admin/           # Admin templates
 .env                 # Environment variables (local)
 .env.example         # Environment template
 .dockerignore        # Docker ignore file
 .gitignore          # Git ignore file
 README.md           # This file
`

##  Configuration

### Environment Variables
- SECRET_KEY: Random string for Flask session security
- ADMIN_USERNAME: Username for admin dashboard access
- ADMIN_PASSWORD: Password for admin dashboard access
- DATABASE_URL: Database connection string (defaults to SQLite)
- FLASK_ENV: Environment (development/production)
- FLASK_DEBUG: Debug mode (true/false)

### Database
- **Type**: SQLite (production-ready for this use case)
- **Location**: wedding.db
- **Migrations**: Handled automatically

##  Features

- **Responsive Design**: Mobile-first with Tailwind CSS
- **Admin Dashboard**: Full CRUD operations for RSVPs with authentication
- **Guest Management**: Add, edit, delete, and track guest responses
- **Real-time Updates**: Live data synchronization
- **Export Functionality**: CSV export for guest data
- **Modern UI**: Clean, professional wedding theme
- **API Endpoints**: RESTful API for integrations

##  Development

### Local Development with Docker

`ash
# Copy environment template
cp .env.example .env

# Edit .env with your local settings
# Start the application
docker-compose up --build

# Or run in background
docker-compose up --build -d
`

**Your app will be available at:**
- **Main Site**: http://localhost:5000
- **Admin Dashboard**: http://localhost:5000/admin

### Manual Development (Without Docker)

`ash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SECRET_KEY="your-secret-key"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="password"

# Run the application
python app.py
`

### Database Management

`ash
# Initialize database
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"

# Or run the app once to auto-create tables
python app.py
`

##  Tech Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, JavaScript, Tailwind CSS
- **Deployment**: Coolify + Docker
- **Authentication**: Flask session-based admin auth
- **Containerization**: Docker & Docker Compose

##  Security

- HTTPS enforced via Coolify/Cloudflare
- Admin authentication required for dashboard access
- CSRF protection on forms
- Secure session management
- Environment variables for sensitive data
- No sensitive data exposed in client-side code

##  Production Deployment

### Coolify Configuration
1. **Repository**: Connect this Git repository
2. **Build Settings**:
   - Build Command: pip install -r requirements.txt
   - Start Command: python app.py
3. **Environment Variables**: Set all required variables
4. **Domains**: Configure your custom domain
5. **SSL**: Automatic via Coolify

### Database Setup
The application uses SQLite which is file-based and doesn't require separate database setup. The database file will be created automatically on first run.

### Backup Strategy
- Database file (wedding.db) contains all guest data
- Regular backups recommended before major updates
- Coolify provides automatic backups of persistent data

##  API Documentation

### Guest Management
- GET /api/guests - Get all guests
- PUT /api/guests/<id> - Update guest RSVP status
- GET /api/stats - Get RSVP statistics

### Admin Access
- /admin/login - Admin login page
- /admin/dashboard - Admin dashboard
- /admin/guests - Guest management
- /admin/export - Export guests to CSV

##  Troubleshooting

### Common Issues
1. **Database Connection**: Ensure DATABASE_URL is set correctly
2. **Static Files**: Check that static files are served correctly
3. **Admin Login**: Verify ADMIN_USERNAME and ADMIN_PASSWORD
4. **Port Issues**: Ensure port 5000 is available

### Logs
Check Coolify logs for application errors and deployment issues.

##  Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

##  License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with  for James & Heather's special day**
