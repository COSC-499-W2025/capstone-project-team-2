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

    INDEX idx_project_versions (project_id, version_number),
    INDEX idx_created_at (created_at),
    
    FOREIGN KEY (project_id) REFERENCES project_data(id) ON DELETE CASCADE,
    UNIQUE KEY unique_project_version (project_id, version_number)
) ENGINE=InnoDB;

DELIMITER //

DROP PROCEDURE IF EXISTS update_project_with_version//

CREATE PROCEDURE update_project_with_version(
    IN p_project_id INT,
    IN p_filename VARCHAR(255),
    IN p_content JSON,
    IN p_file_blob LONGBLOB
)
BEGIN
    DECLARE current_ver INT;
    
    -- Get current version number
    SELECT current_version INTO current_ver 
    FROM project_data 
    WHERE id = p_project_id;
    
    -- Save current state to version history
    INSERT INTO project_versions (project_id, version_number, filename, content, file_blob)
    SELECT id, current_version, filename, content, file_blob
    FROM project_data
    WHERE id = p_project_id;
    
    -- Update to new version
    UPDATE project_data
    SET filename = p_filename,
        content = p_content,
        file_blob = p_file_blob,
        current_version = current_ver + 1
    WHERE id = p_project_id;
END//

-- Restore a previous version
DROP PROCEDURE IF EXISTS restore_project_version//

CREATE PROCEDURE restore_project_version(
    IN p_project_id INT,
    IN p_version_number INT
)
BEGIN
    DECLARE v_filename VARCHAR(255);
    DECLARE v_content JSON;
    DECLARE v_file_blob LONGBLOB;
    DECLARE current_ver INT;
    
    -- Get the version data to restore
    SELECT filename, content, file_blob INTO v_filename, v_content, v_file_blob
    FROM project_versions
    WHERE project_id = p_project_id AND version_number = p_version_number;
    
    -- Get current version number
    SELECT current_version INTO current_ver FROM project_data WHERE id = p_project_id;
    
    -- Save current state before restoring
    INSERT INTO project_versions (project_id, version_number, filename, content, file_blob)
    SELECT id, current_version, filename, content, file_blob
    FROM project_data
    WHERE id = p_project_id;
    
    -- Restore the selected version
    UPDATE project_data
    SET filename = v_filename,
        content = v_content,
        file_blob = v_file_blob,
        current_version = current_ver + 1
    WHERE id = p_project_id;
END//

DELIMITER ;