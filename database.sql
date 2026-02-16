CREATE DATABASE IF NOT EXISTS appdb;

USE appdb;

-- primary project--
CREATE TABLE IF NOT EXISTS project_data (
    Pname VARCHAR(255) NOT NULL,
    content JSON NOT NULL,
    file_blob LONGBLOB,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    current_version INT DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY(Pname, uploaded_at),
    UNIQUE KEY unique_pname (Pname)
) ENGINE=InnoDB;

-- project versions table -- 
CREATE TABLE IF NOT EXISTS project_versions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    project_uploaded_at TIMESTAMP NOT NULL,
    version_number INT NOT NULL,
    content JSON NOT NULL,
    file_blob LONGBLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

 INDEX idx_project_versions (project_name, version_number),
    INDEX idx_created_at (created_at),

    FOREIGN KEY (project_name, project_uploaded_at) 
        REFERENCES project_data(Pname, uploaded_at) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    UNIQUE KEY unique_project_version (project_name, project_uploaded_at, version_number)
) ENGINE=InnoDB;