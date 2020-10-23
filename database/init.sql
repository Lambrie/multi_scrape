CREATE USER google_business_cards_user;
CREATE DATABASE google_business_cards;
GRANT ALL PRIVILEGES ON DATABASE google_business_cards TO google_business_cards_user;
CREATE TABLE business_cards (id SERIAL PRIMARY KEY, cis_name VARCHAR(500),search_names VARCHAR(500),matching_name VARCHAR(500),industry VARCHAR(500));