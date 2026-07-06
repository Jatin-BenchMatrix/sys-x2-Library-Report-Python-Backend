# Risk — Tables

## Main table: `rcsa_risk` (alias `r`)
Primary key: `id` (INT)

| Column | Type | Meaning |
|---|---|---|
| id | INT PK | Risk id |
| `key` | VARCHAR | Reference, e.g. RSK00001 (reserved word — backtick it) |
| title | VARCHAR | Risk title |
| description | TEXT | Risk statement (may contain HTML) |
| businesshierarchy_id | INT FK | Department / entity (→ config_businesshierarchy.id) |
| riskcategory_id | INT FK | Risk category (→ config_riskcategory.id) |
| risktype_id | INT FK | Risk type (→ config_rcsa_risktype.id) |
| status_id | INT FK | Status (→ config_status.id) |
| inherent_id | INT FK | Inherent rating (→ rcsa_assessmentdimensionscale.id) |
| residual_id | INT FK | Residual rating (→ rcsa_assessmentdimensionscale.id) |
| createdon | DATETIME | Created timestamp |

## Lookup tables (id PK, title)
| Table | Use |
|---|---|
| config_businesshierarchy (id, title) | Department |
| config_riskcategory (id, title) | Risk category |
| config_rcsa_risktype (id, title) | Risk type |
| config_status (id, title) | Status |
| rcsa_assessmentdimensionscale (id, title, color) | Inherent / residual rating label + colour |
