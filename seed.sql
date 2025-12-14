-- seed.sql (SQLite)
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS prescriptions;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS medications;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  user_id TEXT PRIMARY KEY,
  full_name TEXT NOT NULL,
  phone TEXT NOT NULL,
  email TEXT NOT NULL,
  preferred_language TEXT NOT NULL CHECK (preferred_language IN ('en', 'he')),
  date_of_birth TEXT NOT NULL,           -- YYYY-MM-DD
  created_at TEXT NOT NULL               -- ISO datetime
);

CREATE TABLE medications (
  medication_id TEXT PRIMARY KEY,
  brand_name TEXT NOT NULL,
  generic_name TEXT NOT NULL,
  active_ingredients_json TEXT NOT NULL, -- JSON string
  form TEXT NOT NULL,
  strength TEXT NOT NULL,
  rx_required INTEGER NOT NULL CHECK (rx_required IN (0,1)),
  usage_instructions TEXT NOT NULL,
  warnings TEXT NOT NULL
);

CREATE TABLE inventory (
  sku TEXT PRIMARY KEY,
  medication_id TEXT NOT NULL REFERENCES medications(medication_id),
  location_id TEXT NOT NULL,
  quantity INTEGER NOT NULL CHECK (quantity >= 0),
  last_updated TEXT NOT NULL
);

CREATE TABLE prescriptions (
  prescription_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(user_id),
  medication_id TEXT NOT NULL REFERENCES medications(medication_id),
  status TEXT NOT NULL CHECK (status IN ('active','expired','cancelled')),
  issued_date TEXT NOT NULL,
  expires_date TEXT,
  refills_remaining INTEGER NOT NULL CHECK (refills_remaining >= 0),
  prescribing_provider TEXT NOT NULL
);

-- 10 synthetic users (made-up)
INSERT INTO users (user_id, full_name, phone, email, preferred_language, date_of_birth, created_at) VALUES
('u_001','Alex Moren','+972-50-000-0001','alex.moren@testmail.local','en','2000-01-15','2025-12-01T10:00:00Z'),
('u_002','Dana Koral','+972-50-000-0002','dana.koral@testmail.local','he','1998-06-22','2025-12-01T10:01:00Z'),
('u_003','Liam Toren','+972-50-000-0003','liam.toren@testmail.local','en','1995-03-09','2025-12-01T10:02:00Z'),
('u_004','Noor Elian','+972-50-000-0004','noor.elian@testmail.local','he','2001-11-30','2025-12-01T10:03:00Z'),
('u_005','Evan Rik','+972-50-000-0005','evan.rik@testmail.local','en','1992-08-04','2025-12-01T10:04:00Z'),
('u_006','Talia Benor','+972-50-000-0006','talia.benor@testmail.local','he','1999-02-18','2025-12-01T10:05:00Z'),
('u_007','Marco Ilan','+972-50-000-0007','marco.ilan@testmail.local','en','1987-12-12','2025-12-01T10:06:00Z'),
('u_008','Rina Sol','+972-50-000-0008','rina.sol@testmail.local','he','2003-05-27','2025-12-01T10:07:00Z'),
('u_009','Oren Vex','+972-50-000-0009','oren.vex@testmail.local','en','1994-09-10','2025-12-01T10:08:00Z'),
('u_010','Mila Daron','+972-50-000-0010','mila.daron@testmail.local','he','1996-07-01','2025-12-01T10:09:00Z');

-- 5 real medications (real brands + generics)
INSERT INTO medications (
  medication_id, brand_name, generic_name, active_ingredients_json,
  form, strength, rx_required, usage_instructions, warnings
) VALUES
(
  'm_001','Tylenol','acetaminophen','["acetaminophen"]',
  'tablet','500 mg',0,
  'Take by mouth according to the product label instructions.',
  'Contains acetaminophen. Exceeding recommended doses may cause severe liver injury.'
),
(
  'm_002','Advil','ibuprofen','["ibuprofen"]',
  'tablet','200 mg',0,
  'Take by mouth with water. Refer to product label for dosing frequency.',
  'NSAID. May increase risk of stomach bleeding or cardiovascular events.'
),
(
  'm_003','Amoxil','amoxicillin','["amoxicillin"]',
  'capsule','500 mg',1,
  'Take exactly as prescribed by a healthcare provider.',
  'Penicillin antibiotic. Allergic reactions can be serious. Prescription only.'
),
(
  'm_004','Ventolin','salbutamol','["salbutamol"]',
  'inhaler','100 mcg/actuation',1,
  'Use by oral inhalation as prescribed.',
  'May cause tremor, nervousness, or increased heart rate. Prescription only.'
),
(
  'm_005','Cortizone-10','hydrocortisone','["hydrocortisone"]',
  'cream','1%',0,
  'Apply a thin layer to the affected area according to label instructions.',
  'For external use only. Avoid contact with eyes.'
);

-- inventory for 2 locations (to test multi-store behavior)
INSERT INTO inventory (sku, medication_id, location_id, quantity, last_updated) VALUES
('sku_H01_001','m_001','IL-HERZLIYA-01',42,'2025-12-14T18:00:00Z'),
('sku_H01_002','m_002','IL-HERZLIYA-01',18,'2025-12-14T18:00:00Z'),
('sku_H01_003','m_003','IL-HERZLIYA-01', 6,'2025-12-14T18:00:00Z'),
('sku_H01_004','m_004','IL-HERZLIYA-01', 0,'2025-12-14T18:00:00Z'),
('sku_H01_005','m_005','IL-HERZLIYA-01',27,'2025-12-14T18:00:00Z'),
('sku_TA1_001','m_001','IL-TELAVIV-01',15,'2025-12-14T18:05:00Z'),
('sku_TA1_002','m_002','IL-TELAVIV-01', 0,'2025-12-14T18:05:00Z'),
('sku_TA1_003','m_003','IL-TELAVIV-01',12,'2025-12-14T18:05:00Z'),
('sku_TA1_004','m_004','IL-TELAVIV-01', 4,'2025-12-14T18:05:00Z'),
('sku_TA1_005','m_005','IL-TELAVIV-01', 9,'2025-12-14T18:05:00Z');

-- sample prescriptions (to demo Rx-required logic)
INSERT INTO prescriptions (
  prescription_id, user_id, medication_id, status, issued_date, expires_date, refills_remaining, prescribing_provider
) VALUES
('rx_1001','u_003','m_003','active','2025-12-01','2026-01-01',0,'Dr. Rowan Hale'),
('rx_1002','u_006','m_004','active','2025-11-20','2026-05-20',2,'Dr. Rowan Hale'),
('rx_1003','u_008','m_003','expired','2025-08-01','2025-09-01',0,'Dr. Rowan Hale'),
('rx_1004','u_002','m_001','cancelled','2025-12-05',NULL,0,'Dr. Rowan Hale');