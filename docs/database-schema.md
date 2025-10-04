# Database Schema Documentation

## Overview
The wedding planner application uses PostgreSQL as the primary database, hosted on Supabase. The schema is designed to handle guest management, RSVP tracking, meal selections, and comprehensive change auditing.

## Tables

### guests
Primary table for storing wedding guest information.

```sql
CREATE TABLE guests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    family_id VARCHAR(100),
    email VARCHAR(255),
    mobile VARCHAR(50),
    address TEXT,
    attending VARCHAR(20) DEFAULT 'maybe',
    meal_choice VARCHAR(100),
    music_requests TEXT,
    restrictions TEXT,
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Field Descriptions
- **id**: Unique identifier (UUID)
- **name**: Full name of the guest
- **family_id**: Groups related guests (e.g., "SMITH", "JONES")
- **email**: Email address for communication
- **mobile**: Phone number
- **address**: Physical address
- **attending**: RSVP status ("yes", "no", "maybe")
- **meal_choice**: Selected meal option
- **music_requests**: Song requests for reception
- **restrictions**: Dietary restrictions or special needs
- **comment**: Admin notes about the guest
- **created_at**: Record creation timestamp
- **updated_at**: Last modification timestamp

#### Constraints & Indexes
```sql
-- Indexes for performance
CREATE INDEX idx_guests_family_id ON guests(family_id);
CREATE INDEX idx_guests_attending ON guests(attending);
CREATE INDEX idx_guests_name ON guests(name);

-- Check constraints
ALTER TABLE guests ADD CONSTRAINT chk_attending 
    CHECK (attending IN ('yes', 'no', 'maybe'));
```

### guest_changes
Audit trail for all guest record modifications.

```sql
CREATE TABLE guest_changes (
    id SERIAL PRIMARY KEY,
    guest_id UUID NOT NULL,
    field_name VARCHAR(50) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    changed_by VARCHAR(100) DEFAULT 'system',
    FOREIGN KEY (guest_id) REFERENCES guests(id) ON DELETE CASCADE
);
```

#### Field Descriptions
- **id**: Sequential identifier
- **guest_id**: Reference to modified guest
- **field_name**: Name of the changed field
- **old_value**: Previous value (as text)
- **new_value**: New value (as text)
- **changed_at**: When the change occurred
- **changed_by**: Who made the change (user/system)

#### Indexes
```sql
CREATE INDEX idx_guest_changes_guest_id ON guest_changes(guest_id);
CREATE INDEX idx_guest_changes_changed_at ON guest_changes(changed_at DESC);
CREATE INDEX idx_guest_changes_field_name ON guest_changes(field_name);
```

## Data Types & Validation

### Attending Values
- `yes`: Confirmed attendance
- `no`: Not attending
- `maybe`: Undecided (default)

### Meal Choices
Common meal options (customizable):
- `chicken`
- `beef`
- `fish`
- `vegetarian`
- `vegan`
- `child_meal`

### Family ID Convention
- Usually surname in uppercase
- Can include numbers for disambiguation
- Examples: "SMITH", "JONES", "BROWN_2"

## Application Constants

### Updatable Columns
Fields that can be modified via the admin interface:

```python
UPDATABLE_COLUMNS = {
    'name', 'family_id', 'email', 'mobile', 'address',
    'attending', 'meal_choice', 'music_requests', 
    'restrictions', 'comment'
}
```

## Common Queries

### Get All Guests
```sql
SELECT id, name, family_id, email, mobile, address, 
       attending, meal_choice, music_requests, restrictions, comment
FROM guests 
ORDER BY name;
```

### Get Guests by Family
```sql
SELECT * FROM guests 
WHERE family_id = %s 
ORDER BY name;
```

### Get Guests Without Family
```sql
SELECT * FROM guests 
WHERE family_id IS NULL OR family_id = '' 
ORDER BY name;
```

### Get Recent Changes
```sql
SELECT gc.*, g.name 
FROM guest_changes gc
JOIN guests g ON gc.guest_id = g.id
ORDER BY gc.changed_at DESC 
LIMIT %s;
```

### Attendance Summary
```sql
SELECT attending, COUNT(*) as count
FROM guests 
GROUP BY attending;
```

### Meal Choice Summary
```sql
SELECT meal_choice, COUNT(*) as count
FROM guests 
WHERE attending = 'yes' AND meal_choice IS NOT NULL
GROUP BY meal_choice;
```

## Database Functions & Triggers

### Update Timestamp Trigger
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_guests_updated_at 
    BEFORE UPDATE ON guests 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

### Change Logging Function
```sql
CREATE OR REPLACE FUNCTION log_guest_changes()
RETURNS TRIGGER AS $$
BEGIN
    -- Log each changed field
    IF OLD.name != NEW.name THEN
        INSERT INTO guest_changes (guest_id, field_name, old_value, new_value)
        VALUES (NEW.id, 'name', OLD.name, NEW.name);
    END IF;
    
    IF OLD.email != NEW.email THEN
        INSERT INTO guest_changes (guest_id, field_name, old_value, new_value)
        VALUES (NEW.id, 'email', OLD.email, NEW.email);
    END IF;
    
    -- Continue for other fields...
    
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER log_guests_changes 
    AFTER UPDATE ON guests 
    FOR EACH ROW 
    EXECUTE FUNCTION log_guest_changes();
```

## Migration Scripts

### Add New Column
```sql
-- Template for adding new columns
ALTER TABLE guests ADD COLUMN new_field_name VARCHAR(255);

-- Update application code to include in UPDATABLE_COLUMNS
-- Update frontend admin table and forms
```

### Data Type Changes
```sql
-- Example: Change meal_choice to allow longer values
ALTER TABLE guests ALTER COLUMN meal_choice TYPE VARCHAR(150);
```

### Index Management
```sql
-- Add new index
CREATE INDEX CONCURRENTLY idx_guests_new_field ON guests(new_field);

-- Drop unused index
DROP INDEX IF EXISTS idx_guests_old_field;
```

## Backup & Recovery

### Backup Command
```bash
pg_dump -h hostname -U username -d database_name > backup.sql
```

### Selective Backup
```bash
pg_dump -h hostname -U username -d database_name -t guests -t guest_changes > guests_backup.sql
```

### Restore Command
```bash
psql -h hostname -U username -d database_name < backup.sql
```

## Performance Considerations

### Query Optimization
- Use appropriate indexes for frequent queries
- Limit result sets with LIMIT clauses
- Use specific column lists instead of SELECT *
- Consider query execution plans for complex queries

### Connection Management
- Use connection pooling in production
- Set appropriate connection timeouts
- Monitor connection usage and limits

### Maintenance Tasks
```sql
-- Analyze tables for query optimization
ANALYZE guests;
ANALYZE guest_changes;

-- Vacuum to reclaim space
VACUUM guests;

-- Reindex if needed
REINDEX TABLE guests;
```

## Security Considerations

### Access Control
- Use dedicated database user for application
- Grant minimal required permissions
- Restrict direct database access

### Data Protection
- Encrypt sensitive data at rest
- Use SSL/TLS for database connections
- Regular security audits and updates

### Audit Trail
- All changes tracked in guest_changes table
- Include timestamps and user information
- Retain change history for compliance

## Monitoring & Alerts

### Key Metrics
- Database connection count
- Query performance and slow queries
- Table sizes and growth
- Failed query attempts

### Health Checks
```sql
-- Check database connectivity
SELECT 1;

-- Check table record counts
SELECT 
    'guests' as table_name, COUNT(*) as count FROM guests
UNION ALL
SELECT 
    'guest_changes' as table_name, COUNT(*) as count FROM guest_changes;

-- Check for data integrity issues
SELECT * FROM guests WHERE name IS NULL OR name = '';
```