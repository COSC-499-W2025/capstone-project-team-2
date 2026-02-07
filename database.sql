CREATE DATABASE IF NOT EXISTS appdb;

USE appdb;

-- primary project--
CREATE TABLE IF NOT EXISTS project_data (
    Pname VARCHAR(255) NOT NULL PRIMARY KEY,
    content JSON NOT NULL,
    file_blob LONGBLOB,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    current_version INT DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_filename (filename)
) ENGINE=InnoDB;

-- project versions table -- 
CREATE TABLE IF NOT EXISTS project_versions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    version_number INT NOT NULL,
    content JSON NOT NULL,
    file_blob LONGBLOB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_project_versions (project_filename, version_number),
    INDEX idx_created_at (created_at),

    FOREIGN KEY (project_filename) REFERENCES project_data(filename) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    UNIQUE KEY unique_project_version (project_filename, version_number)
) ENGINE=InnoDB;