-- StellarNexus Database Initialization

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create repositories table
CREATE TABLE IF NOT EXISTS repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    github_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    description TEXT,
    html_url VARCHAR(500) NOT NULL,
    stars_count INTEGER NOT NULL DEFAULT 0,
    forks_count INTEGER NOT NULL DEFAULT 0,
    language VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    pushed_at TIMESTAMP WITH TIME ZONE,
    size INTEGER,
    archived BOOLEAN DEFAULT FALSE,
    disabled BOOLEAN DEFAULT FALSE,
    created TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create daily_stats table
CREATE TABLE IF NOT EXISTS daily_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID REFERENCES repositories(id),
    date DATE NOT NULL,
    stars_count INTEGER NOT NULL,
    forks_count INTEGER NOT NULL,
    stars_gained INTEGER DEFAULT 0,
    rank INTEGER,
    created TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(repository_id, date)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_repositories_stars ON repositories(stars_count DESC);
CREATE INDEX IF NOT EXISTS idx_repositories_name ON repositories USING gin(name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date DESC);
CREATE INDEX IF NOT EXISTS idx_daily_stats_repository_date ON daily_stats(repository_id, date);

-- Create analytics view
CREATE OR REPLACE VIEW repository_analytics AS
SELECT
    r.id,
    r.name,
    r.full_name,
    r.description,
    r.html_url,
    r.stars_count as current_stars,
    r.language,
    COALESCE(ds.stars_gained, 0) as stars_gained_today,
    ds.rank as current_rank,
    r.created_at as github_created_at,
    r.updated_at as github_updated_at
FROM repositories r
LEFT JOIN daily_stats ds ON r.id = ds.repository_id
    AND ds.date = CURRENT_DATE
ORDER BY r.stars_count DESC;

-- Create function to update repository
CREATE OR REPLACE FUNCTION update_repository_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate stars gained compared to yesterday
    IF OLD.stars_count IS NOT NULL THEN
        NEW.stars_gained = NEW.stars_count - OLD.stars_count;
    END IF;

    -- Update the updated timestamp
    NEW.updated = NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic stats calculation
DROP TRIGGER IF EXISTS update_repository_stats_trigger ON daily_stats;
CREATE TRIGGER update_repository_stats_trigger
    BEFORE INSERT OR UPDATE ON daily_stats
    FOR EACH ROW
    EXECUTE FUNCTION update_repository_stats();

-- Insert some sample data (will be replaced by actual data)
INSERT INTO repositories (github_id, name, full_name, description, html_url, stars_count, language)
VALUES
    (1, 'sample-repo', 'user/sample-repo', 'Sample repository for testing', 'https://github.com/user/sample-repo', 100, 'Python')
ON CONFLICT (github_id) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO stellar;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO stellar;