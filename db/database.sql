CREATE TABLE IF NOT EXISTS ads (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    category VARCHAR(100),
    type VARCHAR(100),
    price INT NULL,
    city VARCHAR(100),
    zipcode VARCHAR(20),
    region VARCHAR(100),
    url TEXT,
    author VARCHAR(64),
    contact VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
