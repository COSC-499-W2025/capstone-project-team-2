-- primary project--
CREATE TABLE IF NOT EXISTS project_data (
    Pname TEXT NOT NULL,
    content TEXT NOT NULL,
    file_blob BLOB,
    uploaded_at TEXT DEFAULT (datetime('now')) NOT NULL,
    current_version INTEGER DEFAULT 1,
    updated_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY(Pname, uploaded_at),
    UNIQUE (Pname)
);

-- project versions table -- 
CREATE TABLE IF NOT EXISTS project_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    project_uploaded_at TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    file_blob BLOB,
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (project_name, project_uploaded_at)
        REFERENCES project_data(Pname, uploaded_at)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    UNIQUE (project_name, project_uploaded_at, version_number)
);

CREATE TRIGGER update_project_data_timestamp
AFTER UPDATE ON project_data
FOR EACH ROW
BEGIN
    UPDATE project_data SET updated_at = datetime('now') WHERE Pname = OLD.Pname;
END;

CREATE INDEX IF NOT EXISTS idx_project_versions ON project_versions (project_name, version_number);
CREATE INDEX IF NOT EXISTS idx_created_at ON project_versions (created_at);