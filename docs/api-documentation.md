# API Documentation

## Overview
The wedding planner application provides a RESTful API for managing guests, retrieving entertainment data, and accessing AI-generated content. All endpoints return JSON responses and use standard HTTP status codes.

## Base URL
- **Local Development**: `http://localhost:5000`
- **Production**: `https://james-and-heather.com`

## Authentication
Currently, the API operates without explicit authentication. Admin functions are protected by the frontend interface.

## Response Format

### Success Response
```json
{
    "success": true,
    "data": { ... },
    "message": "Operation completed successfully"
}
```

### Error Response
```json
{
    "error": "Error description",
    "code": "ERROR_CODE",
    "details": { ... }
}
```

## Guest Management Endpoints

### GET /api/guests
Retrieve all guests with their complete information.

**Response:**
```json
[
    {
        "id": "uuid",
        "name": "John Smith",
        "family_id": "SMITH",
        "email": "john@example.com",
        "mobile": "+1234567890",
        "address": "123 Main St",
        "attending": "yes",
        "meal_choice": "chicken",
        "music_requests": "Dancing Queen",
        "restrictions": "No nuts",
        "comment": "Admin note",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    }
]
```

**Status Codes:**
- `200` - Success
- `500` - Database error

### GET /api/guests/family/{family_id}
Retrieve all guests belonging to a specific family.

**Parameters:**
- `family_id` (string) - Family identifier (e.g., "SMITH")

**Response:**
Same format as `/api/guests` but filtered by family.

**Status Codes:**
- `200` - Success
- `404` - Family not found
- `500` - Database error

### GET /api/guests/no-family
Retrieve guests without an assigned family_id.

**Response:**
Same format as `/api/guests` but only guests with null or empty family_id.

### PATCH /api/guests/{guest_id}
Update one or more fields for a specific guest.

**Parameters:**
- `guest_id` (UUID) - Unique guest identifier

**Request Body:**
```json
{
    "name": "Updated Name",
    "email": "new@example.com",
    "attending": "yes",
    "meal_choice": "vegetarian",
    "restrictions": "Gluten-free"
}
```

**Updatable Fields:**
- `name` - Guest's full name
- `family_id` - Family group identifier
- `email` - Email address
- `mobile` - Phone number
- `address` - Physical address
- `attending` - RSVP status ("yes", "no", "maybe")
- `meal_choice` - Selected meal option
- `music_requests` - Song requests
- `restrictions` - Dietary restrictions
- `comment` - Admin notes

**Response:**
```json
{
    "success": true,
    "updated_fields": ["name", "email"],
    "guest": { ... }
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid request data
- `404` - Guest not found
- `500` - Database error

### GET /api/guest-changes
Retrieve change history for guest records.

**Query Parameters:**
- `limit` (integer, optional) - Maximum number of records (default: 50)
- `guest_id` (UUID, optional) - Filter by specific guest

**Response:**
```json
[
    {
        "id": 1,
        "guest_id": "uuid",
        "guest_name": "John Smith",
        "field_name": "attending",
        "old_value": "maybe",
        "new_value": "yes",
        "changed_at": "2025-01-01T00:00:00Z",
        "changed_by": "admin"
    }
]
```

## Entertainment Endpoints

### GET /api/entertainment/events
Retrieve entertainment events data from external API.

**Response:**
```json
[
    {
        "id": "event_id",
        "title": "Event Title",
        "description": "Event description",
        "date": "2025-01-01",
        "venue": "Venue Name",
        "url": "https://example.com"
    }
]
```

**Caching:** Results are cached to improve performance and reduce external API calls.

### GET /api/entertainment/posts
Retrieve entertainment posts from external sources.

**Response:**
```json
[
    {
        "id": "post_id",
        "title": "Post Title",
        "content": "Post content",
        "author": "Author Name",
        "published_at": "2025-01-01T00:00:00Z",
        "url": "https://example.com"
    }
]
```

## AI Content Endpoints

### GET /api/ai/hen
Get AI-generated content for hen party planning.

**Response:**
```json
{
    "suggestions": [
        {
            "activity": "Spa Day",
            "description": "Relaxing spa treatments",
            "location": "Local spa",
            "cost_estimate": "$200-300 per person"
        }
    ],
    "tips": [
        "Book in advance",
        "Consider dietary restrictions"
    ]
}
```

### GET /api/ai/stag
Get AI-generated content for stag party planning.

**Response:**
Similar format to hen party endpoint with male-oriented activities.

## Error Codes

### HTTP Status Codes
- `200` - OK
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `500` - Internal Server Error

### Application Error Codes
- `INVALID_GUEST_ID` - Guest ID format invalid
- `GUEST_NOT_FOUND` - Guest does not exist
- `INVALID_FIELD` - Field not allowed for updates
- `DATABASE_ERROR` - Database operation failed
- `EXTERNAL_API_ERROR` - External service unavailable

## Rate Limiting
Currently no rate limiting is implemented, but consider implementing for production use.

## Request/Response Examples

### Update Guest Attendance
```bash
curl -X PATCH http://localhost:5000/api/guests/123e4567-e89b-12d3-a456-426614174000 \
  -H "Content-Type: application/json" \
  -d '{"attending": "yes", "meal_choice": "chicken"}'
```

### Get Family Members
```bash
curl http://localhost:5000/api/guests/family/SMITH
```

### Get Recent Changes
```bash
curl http://localhost:5000/api/guest-changes?limit=10
```

## Frontend Integration

### JavaScript Fetch Examples

#### Update Guest
```javascript
async function updateGuest(guestId, updates) {
    try {
        const response = await fetch(`/api/guests/${guestId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updates)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error updating guest:', error);
        throw error;
    }
}
```

#### Fetch Guests
```javascript
async function fetchGuests() {
    try {
        const response = await fetch('/api/guests');
        if (!response.ok) {
            throw new Error('Failed to fetch guests');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching guests:', error);
        return [];
    }
}
```

## Database Integration

### Query Patterns
The API uses raw SQL queries with psycopg for database operations:

```python
def get_guests():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, family_id, email, mobile, address,
                           attending, meal_choice, music_requests, 
                           restrictions, comment, created_at, updated_at
                    FROM guests 
                    ORDER BY name
                """)
                return cur.fetchall()
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise
```

### Change Logging
All guest updates automatically log changes:

```python
def log_guest_change(guest_id, field_name, old_value, new_value):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO guest_changes 
                    (guest_id, field_name, old_value, new_value, changed_by)
                    VALUES (%s, %s, %s, %s, %s)
                """, (guest_id, field_name, old_value, new_value, 'admin'))
                conn.commit()
    except Exception as e:
        logger.error(f"Error logging change: {e}")
```

## Security Considerations

### Input Validation
- All inputs are validated before database operations
- SQL injection protection through parameterized queries
- Field name validation against allowed columns

### Data Sanitization
- Email format validation
- Phone number format checking
- Text field length limits

### Error Handling
- Sensitive information not exposed in error messages
- Proper logging of security-related events
- Graceful degradation on failures

## Performance Optimization

### Caching Strategy
- Entertainment data cached for 1 hour
- Database connection pooling
- Efficient query design with appropriate indexes

### Response Optimization
- Minimal data transfer
- Compression for large responses
- Appropriate HTTP headers for caching

## Testing

### Manual Testing
Use tools like curl or Postman to test endpoints:

```bash
# Test guest update
curl -X PATCH http://localhost:5000/api/guests/guest-id \
  -H "Content-Type: application/json" \
  -d '{"attending": "yes"}'

# Test error handling
curl -X PATCH http://localhost:5000/api/guests/invalid-id \
  -H "Content-Type: application/json" \
  -d '{"invalid_field": "value"}'
```

### Automated Testing
Consider implementing:
- Unit tests for each endpoint
- Integration tests with test database
- Load testing for performance validation

## Future Enhancements

### Planned Features
- Authentication and authorization
- Rate limiting and throttling
- API versioning
- Enhanced error reporting
- WebSocket support for real-time updates

### Performance Improvements
- Redis caching layer
- Database query optimization
- Response compression
- CDN integration for static assets