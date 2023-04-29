CREATE TABLE IF NOT EXISTS authorization_code (
    code TEXT PRIMARY KEY,
    created TIMESTAMP WITH TIME ZONE DEFAULT now()
);
