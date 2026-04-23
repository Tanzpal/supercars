-- Database Setup for CarsBay
CREATE DATABASE IF NOT EXISTS supercars_db;
USE supercars_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    is_admin TINYINT(1) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(100),
    name VARCHAR(100),
    phone VARCHAR(20),
    vehicle VARCHAR(100),
    date DATE,
    time VARCHAR(20),
    area VARCHAR(100),
    city VARCHAR(50),
    state VARCHAR(50),
    post_code VARCHAR(20),
    driving_license VARCHAR(255),
    license_number VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS contact_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    query TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS resale_cars (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    chassis VARCHAR(100),
    plate VARCHAR(50),
    rc_image VARCHAR(255),
    car_image VARCHAR(255),
    years_used INT,
    owners INT,
    is_verified TINYINT(1) DEFAULT 0,
    blockchain_id VARCHAR(255),
    health_score INT
);

CREATE TABLE IF NOT EXISTS wishlist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(100),
    car_name VARCHAR(100),
    car_image VARCHAR(255),
    car_link VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS ownership (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT,
    user_id INT,
    shares INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES resale_cars(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
