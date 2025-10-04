# Wedding Planner Application Architecture

## Overview
A Flask-based wedding planning application with PostgreSQL database, deployed using Docker containers with Cloudflare tunnel for external access.

## Technology Stack

### Backend
- **Framework**: Flask 3.0.3 (Python 3.11)
- **Database**: PostgreSQL (via Supabase)
- **ORM**: Raw SQL with psycopg[binary] 3.2.10
- **Server**: Gunicorn 21.2.0 for production
- **Environment**: Python-dotenv for configuration

### Frontend
- **Templates**: Jinja2 templating engine
- **Styling**: Custom CSS with responsive design
- **JavaScript**: Vanilla JS with modern ES6+ features
- **UI Components**: Custom modal popups, tables, forms

### Infrastructure
- **Containerization**: Docker with docker-compose
- **External Access**: Cloudflare Tunnel
- **Deployment**: Multi-container setup (web + tunnel)

## Application Structure

```
wedding-planner/
├── app.py                    # Main Flask application
├── templates/
│   └── index.html           # Single-page application
├── static/
│   └── images/              # Static assets
├── utils/
│   ├── db.py               # Database utilities
│   └── entertainment_cache.py # Caching utilities
├── scripts/                 # Database management scripts
├── docker-compose.yml       # Container orchestration
├── Dockerfile              # Container definition
└── requirements.txt        # Python dependencies
```

## Core Features

### 1. Guest Management System
- **CRUD Operations**: Create, read, update, delete guests
- **Family Grouping**: Guests organized by family_id
- **Admin Interface**: Table-based management with inline editing
- **Detailed Editing**: Modal popup for comprehensive guest data editing

### 2. RSVP & Meal Selection
- **Attendance Tracking**: Yes/No/Maybe responses
- **Meal Preferences**: Multiple meal options with dietary restrictions
- **Validation**: Server-side validation for meal selections
- **Guest Portal**: Public interface for guests to update their information

### 3. Event Information
- **Static Content**: Wedding details, venue information
- **Entertainment Integration**: External API for entertainment events
- **AI-Generated Content**: Hen/stag party suggestions
- **Image Gallery**: Static image assets for different sections

### 4. Admin Features
- **Guest Table**: Sortable, filterable table with 10 columns
- **Change Tracking**: Complete audit log of all guest modifications
- **Bulk Operations**: Multi-field updates via PATCH API
- **Export Capabilities**: Data export for external use

## Database Schema

### Main Tables

#### `guests` Table
```sql
- id (UUID, Primary Key)
- name (VARCHAR)
- family_id (VARCHAR) 
- email (VARCHAR)
- mobile (VARCHAR)
- address (TEXT)
- attending (VARCHAR) - 'yes', 'no', 'maybe'
- meal_choice (VARCHAR)
- music_requests (TEXT)
- restrictions (TEXT)
- comment (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

#### `guest_changes` Table
```sql
- id (SERIAL, Primary Key)
- guest_id (UUID, Foreign Key)
- field_name (VARCHAR)
- old_value (TEXT)
- new_value (TEXT)
- changed_at (TIMESTAMP)
- changed_by (VARCHAR)
```

## API Endpoints

### Guest Management
- `GET /api/guests` - List all guests
- `GET /api/guests/family/{family_id}` - Get guests by family
- `GET /api/guests/no-family` - Get guests without family
- `PATCH /api/guests/{id}` - Update guest (supports multiple fields)
- `GET /api/guest-changes` - Get change history

### Entertainment & AI
- `GET /api/entertainment/events` - External entertainment data
- `GET /api/entertainment/posts` - Entertainment posts
- `GET /api/ai/hen` - AI-generated hen party content
- `GET /api/ai/stag` - AI-generated stag party content

## Key Design Patterns

### 1. Single Page Application (SPA)
- All functionality in one HTML template
- JavaScript-driven navigation between sections
- Dynamic content loading via AJAX

### 2. RESTful API Design
- Standard HTTP methods (GET, PATCH, POST, DELETE)
- JSON request/response format
- Consistent error handling

### 3. Component-Based Frontend
- Reusable JavaScript functions
- Modular CSS classes
- Separation of concerns

### 4. Database Abstraction
- Utility functions in `utils/db.py`
- Parameterized queries for security
- Connection pooling and error handling

## Security Considerations

### Data Protection
- Environment variables for sensitive data
- Parameterized SQL queries prevent injection
- Input validation on both client and server

### Access Control
- Admin sections require authentication
- Guest data access controls
- Change tracking for accountability

## Performance Optimizations

### Caching
- Entertainment data caching
- Static asset optimization
- Database query optimization

### Frontend Optimization
- Debounced auto-save functionality
- Efficient DOM manipulation
- Minimal external dependencies

## Deployment Architecture

### Docker Configuration
```yaml
services:
  web:
    - Flask application
    - Port 5000 internal
    - Environment variables
  
  tunnel:
    - Cloudflare tunnel
    - External access
    - SSL termination
```

### Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `CLOUDFLARE_TUNNEL_TOKEN` - Tunnel authentication
- `FLASK_ENV` - Environment configuration

## Development Workflow

### Local Development
1. Docker compose for consistent environment
2. Hot reloading for development
3. Database scripts for schema management

### Production Deployment
1. Container build and push
2. Cloudflare tunnel for external access
3. Environment-specific configurations

## Monitoring & Maintenance

### Logging
- Flask application logs
- Database query logging
- Error tracking and alerts

### Backup Strategy
- Database backup procedures
- Static asset backup
- Configuration backup

## Future Enhancements

### Planned Features
- Email notifications for RSVP changes
- Advanced reporting and analytics
- Mobile-responsive optimizations
- Integration with external wedding services

### Technical Improvements
- Redis caching layer
- API rate limiting
- Enhanced security measures
- Performance monitoring