# AI Assistant Prompts & Guidelines

## System Context
This is a Flask-based wedding planning application with a PostgreSQL database, containerized with Docker, and accessible via Cloudflare tunnel. The application manages wedding guests, RSVPs, meal selections, and provides admin tools for event management.

## Code Style & Conventions

### Python (Flask Backend)
- **Framework**: Flask 3.0.3 with Jinja2 templating
- **Database**: Raw SQL with psycopg[binary] 3.2.10 (no ORM)
- **Style**: PEP 8 compliant, descriptive variable names
- **Error Handling**: Try-catch blocks with proper logging
- **Security**: Parameterized queries, input validation

### JavaScript (Frontend)
- **Style**: Modern ES6+ syntax, const/let over var
- **Functions**: Arrow functions preferred for callbacks
- **DOM**: querySelector/querySelectorAll over jQuery
- **Async**: Fetch API for HTTP requests
- **Error Handling**: Proper try-catch with user feedback

### HTML/CSS
- **Structure**: Semantic HTML5 elements
- **Styling**: CSS custom properties (variables)
- **Responsive**: Mobile-first design approach
- **Accessibility**: ARIA labels, semantic markup

## Common Development Patterns

### Database Operations
```python
# Standard pattern for database queries
def get_guests():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM guests ORDER BY name")
                return cur.fetchall()
    except Exception as e:
        logger.error(f"Error fetching guests: {e}")
        return []
```

### API Endpoints
```python
# RESTful API pattern
@app.route('/api/guests/<guest_id>', methods=['PATCH'])
def update_guest(guest_id):
    try:
        data = request.get_json()
        # Validate input
        # Update database
        # Log changes
        # Return response
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

### Frontend AJAX Patterns
```javascript
// Standard fetch pattern
async function updateGuest(guestId, data) {
    try {
        const response = await fetch(`/api/guests/${guestId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) throw new Error('Update failed');
        
        const result = await response.json();
        showToast('Guest updated successfully', 'success');
        return result;
    } catch (error) {
        showToast('Error updating guest', 'error');
        console.error('Update error:', error);
    }
}
```

## Key Files & Their Purposes

### Core Application Files
- **`app.py`** - Main Flask application, all routes and business logic
- **`templates/index.html`** - Single-page application template
- **`utils/db.py`** - Database connection and utility functions
- **`utils/entertainment_cache.py`** - External API caching logic

### Configuration Files
- **`docker-compose.yml`** - Container orchestration
- **`Dockerfile`** - Container build instructions
- **`requirements.txt`** - Python dependencies
- **`.env`** - Environment variables (not in repo)

### Database Scripts
- **`scripts/create_supabase_table.py`** - Database schema creation
- **`scripts/import_supabase.py`** - Data import utilities
- **`scripts/add_column.py`** - Schema migration helper

## Feature Implementation Guidelines

### Adding New Guest Fields
1. Update database schema in `scripts/add_column.py`
2. Add field to `UPDATABLE_COLUMNS` in `app.py`
3. Update admin table in `templates/index.html`
4. Add to guest popup modal if needed
5. Test with both inline and popup editing

### Creating New API Endpoints
1. Define route in `app.py` following RESTful conventions
2. Implement proper error handling and validation
3. Add logging for important operations
4. Update frontend JavaScript if needed
5. Test with different input scenarios

### Adding New Frontend Features
1. Add HTML structure in appropriate section
2. Style with CSS following existing patterns
3. Implement JavaScript functionality
4. Add error handling and user feedback
5. Ensure responsive design works

## Database Best Practices

### Query Patterns
```sql
-- Always use parameterized queries
SELECT * FROM guests WHERE family_id = %s AND attending = %s

-- Include proper ordering
SELECT * FROM guest_changes ORDER BY changed_at DESC LIMIT %s

-- Use specific columns when possible
SELECT name, email, attending FROM guests WHERE id = %s
```

### Change Tracking
- All guest updates should log changes to `guest_changes` table
- Include old and new values for audit trail
- Track timestamp and source of changes

## Frontend UI Patterns

### Modal Popups
- Use existing modal structure for consistency
- Include proper close functionality
- Handle escape key and overlay clicks
- Prevent body scrolling when open

### Form Validation
- Client-side validation for immediate feedback
- Server-side validation for security
- Clear error messages for users
- Highlight invalid fields

### Toast Notifications
- Success messages for completed actions
- Error messages for failures
- Auto-dismiss after appropriate time
- Consistent positioning and styling

## Common Debugging Approaches

### Backend Issues
1. Check Flask logs for errors
2. Verify database connections
3. Test SQL queries independently
4. Check environment variables
5. Validate request data format

### Frontend Issues
1. Use browser developer tools
2. Check console for JavaScript errors
3. Verify network requests in Network tab
4. Test responsive design at different screen sizes
5. Validate HTML structure

### Database Issues
1. Check connection string and credentials
2. Verify table schema matches code expectations
3. Test queries in database client
4. Check for constraint violations
5. Monitor connection pool usage

## Deployment Considerations

### Docker Environment
- Use `docker-compose up --build` for fresh builds
- Check container logs for runtime issues
- Ensure environment variables are properly set
- Verify network connectivity between containers

### Production Checklist
- Environment variables configured
- Database migrations applied
- Static assets optimized
- SSL/TLS properly configured
- Monitoring and logging enabled

## Testing Strategies

### Manual Testing
- Test all CRUD operations for guests
- Verify admin table functionality
- Test responsive design on mobile
- Check external API integrations
- Validate form submissions

### Automated Testing Considerations
- Unit tests for utility functions
- Integration tests for API endpoints
- Frontend testing for user interactions
- Database testing for data integrity

## Performance Optimization

### Database Optimization
- Use appropriate indexes
- Limit query results when possible
- Cache frequently accessed data
- Monitor query performance

### Frontend Optimization
- Minimize DOM manipulations
- Use debouncing for frequent operations
- Optimize images and assets
- Implement lazy loading where appropriate

## Security Guidelines

### Input Validation
- Sanitize all user inputs
- Validate data types and ranges
- Check for SQL injection attempts
- Implement CSRF protection

### Data Protection
- Use HTTPS for all communications
- Encrypt sensitive data at rest
- Implement proper session management
- Regular security audits

## Common Gotchas & Solutions

### Database Connection Issues
- Always use connection pooling
- Handle connection timeouts gracefully
- Close connections properly
- Monitor connection counts

### Frontend State Management
- Keep UI state synchronized with server
- Handle concurrent updates gracefully
- Implement optimistic updates where appropriate
- Provide clear loading states

### Responsive Design
- Test on actual mobile devices
- Use flexible grid systems
- Optimize touch interactions
- Consider mobile-specific features

## When to Ask for Help

### Complex Database Operations
- Multi-table transactions
- Performance optimization
- Schema migrations
- Data integrity issues

### Advanced Frontend Features
- Complex user interactions
- Performance optimization
- Accessibility improvements
- Browser compatibility

### Security Concerns
- Authentication implementation
- Data protection requirements
- Vulnerability assessments
- Compliance requirements