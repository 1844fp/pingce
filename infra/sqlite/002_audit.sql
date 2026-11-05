CREATE TABLE audit_events(seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL UNIQUE, project TEXT NOT NULL, action TEXT NOT NULL, resource_id TEXT NOT NULL, metadata TEXT NOT NULL, created REAL NOT NULL, previous_sha TEXT NOT NULL, sha256 TEXT NOT NULL);
CREATE INDEX audit_project_order ON audit_events(project,seq);
