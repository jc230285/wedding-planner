# Wedding Planner Project Documentation

This documentation provides comprehensive information about the wedding planner application, including architecture, development guidelines, and deployment procedures.

## 📋 Table of Contents

### Core Documentation
- [**Architecture Overview**](architecture.md) - System design, technology stack, and application structure
- [**Database Schema**](database-schema.md) - Complete database documentation with tables, relationships, and queries
- [**API Documentation**](api-documentation.md) - RESTful API endpoints, request/response formats, and integration examples
- [**Deployment Guide**](deployment-guide.md) - Step-by-step deployment instructions using Docker and Cloudflare

### Development Resources
- [**AI Assistant Prompts**](ai-prompts.md) - Guidelines for AI-assisted development, coding patterns, and best practices

## 🚀 Quick Start

### For Developers
1. Review the [Architecture Overview](architecture.md) to understand the system design
2. Check the [AI Prompts Guide](ai-prompts.md) for coding standards and patterns
3. Refer to [Database Schema](database-schema.md) for data structure understanding
4. Use [API Documentation](api-documentation.md) for endpoint integration

### For Deployment
1. Follow the [Deployment Guide](deployment-guide.md) for complete setup instructions
2. Ensure all prerequisites are met (Docker, environment variables, etc.)
3. Use the provided Docker configuration for consistent deployment

## 🏗️ Application Overview

### Technology Stack
- **Backend**: Flask 3.0.3 (Python 3.11)
- **Database**: PostgreSQL via Supabase
- **Frontend**: Vanilla JavaScript with modern ES6+
- **Deployment**: Docker with Cloudflare tunnel
- **Styling**: Custom CSS with responsive design

### Key Features
- **Guest Management**: Complete CRUD operations for wedding guests
- **Admin Interface**: Table-based management with inline editing
- **RSVP System**: Attendance tracking and meal selection
- **Change Auditing**: Complete history of all guest modifications
- **Entertainment Integration**: External API for event information
- **AI Content**: Generated suggestions for hen/stag parties

## 📊 Database Structure

### Primary Tables
- **`guests`** - Main guest information and RSVP data
- **`guest_changes`** - Audit trail for all modifications

### Key Relationships
- One-to-many: Guest to Changes
- Grouping: Guests by family_id for family management

## 🔌 API Endpoints

### Guest Management
- `GET /api/guests` - Retrieve all guests
- `PATCH /api/guests/{id}` - Update guest information
- `GET /api/guest-changes` - View change history

### Entertainment & AI
- `GET /api/entertainment/events` - External entertainment data
- `GET /api/ai/hen` - AI-generated hen party content
- `GET /api/ai/stag` - AI-generated stag party content

## 🐳 Docker Deployment

### Services
- **web**: Flask application container
- **tunnel**: Cloudflare tunnel for external access

### Quick Deploy
```bash
docker-compose up --build -d
```

### Access Points
- **Local**: http://localhost:5000
- **External**: https://your-domain.com (via tunnel)

## 🔧 Development Guidelines

### Code Standards
- Python: PEP 8 compliant with descriptive naming
- JavaScript: Modern ES6+ with const/let preferences
- HTML: Semantic HTML5 with accessibility considerations
- CSS: Custom properties and mobile-first responsive design

### Security Practices
- Parameterized SQL queries to prevent injection
- Input validation on both client and server
- Environment variables for sensitive configuration
- Comprehensive change logging for accountability

## 🚀 Performance Features

### Optimization Strategies
- Database connection pooling
- External API caching (entertainment data)
- Debounced auto-save functionality
- Efficient DOM manipulation patterns

### Monitoring Capabilities
- Application logging for debugging
- Change tracking for audit trails
- Docker container health monitoring
- Database query performance tracking

## 🔐 Security Considerations

### Data Protection
- SSL/TLS encryption via Cloudflare tunnel
- Secure database connections with credentials management
- Input sanitization and validation
- Regular security updates and patches

### Access Control
- Admin interface protection
- Guest data access restrictions
- Change logging for accountability
- Environment-based configuration management

## 📈 Future Enhancements

### Planned Features
- Email notifications for RSVP changes
- Advanced reporting and analytics
- Mobile application development
- Integration with external wedding services

### Technical Improvements
- Redis caching layer implementation
- API rate limiting and throttling
- Enhanced monitoring and alerting
- Automated testing suite development

## 🤝 Contributing

### Development Workflow
1. Review existing documentation thoroughly
2. Follow established coding patterns and conventions
3. Test changes in Docker environment
4. Update documentation for new features
5. Ensure proper error handling and logging

### Documentation Updates
- Keep all documentation current with code changes
- Update API documentation for new endpoints
- Maintain deployment guide accuracy
- Include security considerations for new features

## 📞 Support & Maintenance

### Common Tasks
- Database backup and restoration procedures
- Application log monitoring and analysis
- Docker container management and updates
- Security patch application and testing

### Troubleshooting Resources
- Check application logs for error details
- Verify database connectivity and performance
- Monitor container health and resource usage
- Review Cloudflare tunnel status and configuration

## 📝 Documentation Maintenance

This documentation is maintained alongside the codebase to ensure accuracy and relevance. Each major feature addition or system change should include corresponding documentation updates.

### Update Checklist
- [ ] Architecture changes reflected in overview
- [ ] New database fields added to schema documentation
- [ ] API changes documented with examples
- [ ] Deployment procedures tested and updated
- [ ] AI prompts updated with new patterns and guidelines

---

For specific technical details, please refer to the individual documentation files linked above. Each document provides comprehensive information for its respective area of the application.