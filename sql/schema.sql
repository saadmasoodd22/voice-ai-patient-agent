-- Northstar patient registry (MySQL 8)
-- Safe to run on the voice_ai database only.

CREATE DATABASE IF NOT EXISTS voice_ai
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE voice_ai;

CREATE TABLE IF NOT EXISTS patients (
  patient_id CHAR(36) NOT NULL PRIMARY KEY,
  first_name VARCHAR(50) NOT NULL,
  last_name VARCHAR(50) NOT NULL,
  date_of_birth DATE NOT NULL,
  sex VARCHAR(32) NOT NULL,
  phone_number VARCHAR(10) NOT NULL,
  email VARCHAR(255) NULL,
  address_line_1 VARCHAR(255) NOT NULL,
  address_line_2 VARCHAR(255) NULL,
  city VARCHAR(100) NOT NULL,
  state CHAR(2) NOT NULL,
  zip_code VARCHAR(10) NOT NULL,
  insurance_provider VARCHAR(255) NULL,
  insurance_member_id VARCHAR(64) NULL,
  preferred_language VARCHAR(50) NOT NULL DEFAULT 'English',
  emergency_contact_name VARCHAR(100) NULL,
  emergency_contact_phone VARCHAR(10) NULL,
  created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
  updated_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP() ON UPDATE UTC_TIMESTAMP(),
  deleted_at DATETIME NULL,
  INDEX ix_patients_last_name (last_name),
  INDEX ix_patients_dob (date_of_birth),
  INDEX ix_patients_phone (phone_number),
  INDEX ix_patients_deleted (deleted_at)
);

CREATE TABLE IF NOT EXISTS call_logs (
  id CHAR(36) NOT NULL PRIMARY KEY,
  patient_id CHAR(36) NULL,
  vapi_call_id VARCHAR(64) NULL,
  caller_number VARCHAR(20) NULL,
  transcript TEXT NULL,
  collected_payload JSON NULL,
  outcome VARCHAR(32) NOT NULL DEFAULT 'in_progress',
  created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
  INDEX ix_call_logs_patient (patient_id)
);
