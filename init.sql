-- Initial database setup for docker-compose
-- Creates sample tables for testing and examples

CREATE DATABASE IF NOT EXISTS test_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE test_db;

-- Sample users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    age INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    balance DECIMAL(10, 2) DEFAULT 0.00,
    INDEX idx_email (email),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sample products table with JSON
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    specs JSON,
    stock INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sample embeddings table for RAG/AI use cases
CREATE TABLE IF NOT EXISTS embeddings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    text TEXT NOT NULL,
    embedding JSON,  -- Store vector as JSON array
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert sample data
INSERT INTO users (name, email, age, metadata, balance) VALUES
('Alice Johnson', 'alice@example.com', 30, '{"role": "admin", "verified": true}', 1250.50),
('Bob Smith', 'bob@example.com', 25, '{"role": "user", "verified": false}', 750.00),
('Charlie Brown', 'charlie@example.com', 35, '{"role": "user", "verified": true}', 2100.75);

INSERT INTO products (name, price, specs, stock) VALUES
('Laptop Pro', 1299.99, '{"cpu": "Intel i7", "ram": "16GB", "storage": "512GB SSD"}', 15),
('Wireless Mouse', 29.99, '{"dpi": "1600", "wireless": true, "battery": "AA"}', 50),
('USB-C Cable', 12.99, '{"length": "2m", "speed": "USB 3.1", "color": "black"}', 100);
