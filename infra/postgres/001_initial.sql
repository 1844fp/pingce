-- PostgreSQL schema v1; apply once to an empty isolated destination.
BEGIN;
CREATE TABLE resources (
 id TEXT PRIMARY KEY, project TEXT NOT NULL, kind TEXT NOT NULL,
 name TEXT NOT NULL, body JSONB NOT NULL, created DOUBLE PRECISION NOT NULL);
CREATE TABLE runs (
 id TEXT PRIMARY KEY, project TEXT NOT NULL, name TEXT NOT NULL,
 spec JSONB NOT NULL, status TEXT NOT NULL, created DOUBLE PRECISION NOT NULL,
 updated DOUBLE PRECISION NOT NULL, idem TEXT NOT NULL, digest TEXT NOT NULL,
 error TEXT, UNIQUE(project, idem));
CREATE TABLE results (
 id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id),
 case_id TEXT NOT NULL, repetition BIGINT NOT NULL, body JSONB NOT NULL,
 UNIQUE(run_id,case_id,repetition));
CREATE TABLE reviews (
 id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id),
 case_id TEXT NOT NULL, repetition BIGINT NOT NULL,
 decision TEXT NOT NULL, reason TEXT NOT NULL, created DOUBLE PRECISION NOT NULL);
COMMIT;
