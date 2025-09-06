-- PostgreSQL Specific Query Examples

-- JSON operations (PostgreSQL specific)
-- Query JSON fields
SELECT id, data->>'name' as name, data->>'age' as age 
FROM user_profiles 
WHERE data->>'status' = 'active';

-- JSON array operations
SELECT id, jsonb_array_elements_text(data->'tags') as tag
FROM posts 
WHERE data ? 'tags';

-- Full text search
-- Basic text search
SELECT * FROM posts 
WHERE to_tsvector('english', title || ' ' || content) @@ to_tsquery('english', 'database');

-- Text search with ranking
SELECT *, ts_rank(to_tsvector('english', title || ' ' || content), query) as rank
FROM posts, to_tsquery('english', 'database') query
WHERE to_tsvector('english', title || ' ' || content) @@ query
ORDER BY rank DESC;

-- Advanced date operations
-- Extract parts of dates
SELECT 
    EXTRACT(year FROM created_at) as year,
    EXTRACT(month FROM created_at) as month,
    COUNT(*) as count
FROM posts
GROUP BY year, month
ORDER BY year DESC, month DESC;

-- Date truncation
SELECT 
    date_trunc('week', created_at) as week,
    COUNT(*) as posts_per_week
FROM posts
GROUP BY week
ORDER BY week DESC;

-- Array operations
-- Working with arrays
SELECT * FROM users 
WHERE 'admin' = ANY(roles);

-- Array aggregation
SELECT 
    category,
    array_agg(title) as titles
FROM posts
GROUP BY category;

-- Regular expressions
-- Pattern matching with regex
SELECT * FROM users 
WHERE email ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$';

-- Common Table Expressions (CTEs)
-- Recursive CTE for hierarchical data
WITH RECURSIVE category_tree AS (
    -- Base case: top-level categories
    SELECT id, name, parent_id, 1 as level
    FROM categories 
    WHERE parent_id IS NULL
    
    UNION ALL
    
    -- Recursive case: child categories
    SELECT c.id, c.name, c.parent_id, ct.level + 1
    FROM categories c
    INNER JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree ORDER BY level, name;

-- Window functions for analytics
-- Moving averages
SELECT 
    date,
    value,
    AVG(value) OVER (
        ORDER BY date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as moving_avg_7_days
FROM daily_metrics
ORDER BY date;

-- Percentiles
SELECT 
    user_id,
    score,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY score) OVER () as median_score,
    PERCENT_RANK() OVER (ORDER BY score) as percentile_rank
FROM user_scores;

-- Advanced aggregations
-- Statistical functions
SELECT 
    category,
    COUNT(*) as count,
    AVG(price) as avg_price,
    STDDEV(price) as price_stddev,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price) as q1,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price) as q3
FROM products
GROUP BY category;

-- UPSERT operations
-- Insert or update on conflict
INSERT INTO user_stats (user_id, login_count, last_login)
VALUES (123, 1, NOW())
ON CONFLICT (user_id)
DO UPDATE SET 
    login_count = user_stats.login_count + 1,
    last_login = NOW();

-- Materialized views
-- Create materialized view for complex aggregations
CREATE MATERIALIZED VIEW user_activity_summary AS
SELECT 
    u.id,
    u.name,
    COUNT(p.id) as post_count,
    COUNT(c.id) as comment_count,
    MAX(p.created_at) as last_post,
    MAX(c.created_at) as last_comment
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
LEFT JOIN comments c ON u.id = c.user_id
GROUP BY u.id, u.name;

-- Refresh materialized view
REFRESH MATERIALIZED VIEW user_activity_summary;
