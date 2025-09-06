-- Common SQL Query Examples

-- Basic SELECT operations
-- Get all records from a table
SELECT * FROM users;

-- Get specific columns
SELECT id, name, email FROM users;

-- Get records with conditions
SELECT * FROM users WHERE age > 18;

-- Get records with multiple conditions
SELECT * FROM users WHERE age > 18 AND status = 'active';

-- JOIN operations
-- Inner join between two tables
SELECT u.name, p.title 
FROM users u 
INNER JOIN posts p ON u.id = p.user_id;

-- Left join to include all users even without posts
SELECT u.name, p.title 
FROM users u 
LEFT JOIN posts p ON u.id = p.user_id;

-- Aggregation queries
-- Count records
SELECT COUNT(*) FROM users;

-- Count with grouping
SELECT status, COUNT(*) 
FROM users 
GROUP BY status;

-- Average, sum, min, max
SELECT 
    AVG(age) as average_age,
    MIN(age) as youngest,
    MAX(age) as oldest,
    COUNT(*) as total_users
FROM users;

-- Subqueries
-- Users who have made posts
SELECT * FROM users 
WHERE id IN (SELECT DISTINCT user_id FROM posts);

-- Users with above average age
SELECT * FROM users 
WHERE age > (SELECT AVG(age) FROM users);

-- Date and time queries
-- Records from last 30 days
SELECT * FROM posts 
WHERE created_at >= NOW() - INTERVAL '30 days';

-- Records grouped by date
SELECT DATE(created_at) as date, COUNT(*) 
FROM posts 
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Sorting and limiting
-- Top 10 most recent posts
SELECT * FROM posts 
ORDER BY created_at DESC 
LIMIT 10;

-- Pagination
SELECT * FROM posts 
ORDER BY created_at DESC 
LIMIT 10 OFFSET 20;

-- String operations
-- Search for partial matches
SELECT * FROM users 
WHERE name ILIKE '%john%';

-- Multiple pattern matching
SELECT * FROM users 
WHERE email LIKE '%@gmail.com' OR email LIKE '%@yahoo.com';

-- Update operations
-- Update single record
UPDATE users 
SET status = 'inactive' 
WHERE id = 123;

-- Update multiple records
UPDATE users 
SET last_login = NOW() 
WHERE status = 'active';

-- Delete operations
-- Delete specific record
DELETE FROM posts 
WHERE id = 456;

-- Delete with conditions
DELETE FROM users 
WHERE status = 'inactive' AND last_login < NOW() - INTERVAL '1 year';

-- Complex queries with window functions
-- Rank users by post count
SELECT 
    u.name,
    COUNT(p.id) as post_count,
    RANK() OVER (ORDER BY COUNT(p.id) DESC) as rank
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
GROUP BY u.id, u.name
ORDER BY rank;

-- Running totals
SELECT 
    date,
    daily_count,
    SUM(daily_count) OVER (ORDER BY date) as running_total
FROM (
    SELECT 
        DATE(created_at) as date,
        COUNT(*) as daily_count
    FROM posts
    GROUP BY DATE(created_at)
) daily_stats
ORDER BY date;
