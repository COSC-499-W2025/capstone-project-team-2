CREATE DATABASE IF NOT EXISTS appdb;

USE appdb;

-- primary project--
CREATE TABLE IF NOT EXISTS project_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    content JSON NOT NULL,
    file_blob LONGBLOB,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    current_version INT DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_filename (filename)
) ENGINE=InnoDB;

-- project history table--
CREATE TABLE IF NOT EXISTS project_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    version_number INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    content JSON NOT NULL,
    file_blob LONGBLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

);

