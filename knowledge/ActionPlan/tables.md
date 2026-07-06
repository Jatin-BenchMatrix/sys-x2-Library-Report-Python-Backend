# Action Plan — Tables

## Main table: `ap_actionplan` (alias `ap`)
Primary key: `id` (INT)

| Column | Type | Meaning |
|---|---|---|
| id | INT PK | Action plan id |
| ref_key | VARCHAR | Human reference, e.g. AP00001 |
| title | VARCHAR | Action title |
| description | TEXT | What needs to be done |
| business_hierarchy_id | INT FK | Department / entity (→ config_businesshierarchy.id) |
| assigned_to_id | INT FK | Owner / assignee (→ config_user.ID) |
| responsible_person | INT FK | Responsible person (→ config_user.ID) |
| action_plan_type_id | INT FK | Type (→ ap_action_plan_type.id) |
| action_plan_severity_id | INT FK | Severity / priority (→ ap_action_plan_severity.id) |
| action_plan_category_id | INT FK | Category (→ ap_action_plan_category.id) |
| resolution_type_id | INT FK | Resolution type (→ ap_resolution_type.id) |
| source_of_finding_id | INT FK | Source of finding (→ source_of_finding.id) |
| status_id | INT FK | Workflow status (→ config_status.id) |
| start_date | DATE | Start date |
| expected_completion_date | DATE | Target / due date |
| actual_completion_date | DATE | Actual completion date (NULL = not completed) |
| owner_target_date | DATE | Owner's committed date |
| reschedule_date | DATE | Rescheduled date |
| closure_date | DATE | Closure date (NULL = not closed) |
| amount | NUMERIC(18,5) | Monetary amount |
| created_on | DATETIME | Created timestamp |

## Lookup tables (each has `id` PK and `title`)
| Table | Use |
|---|---|
| config_businesshierarchy (id, title) | Department / entity name |
| config_user (ID, USER_NAME) | Owner / responsible person name — **PK is `ID`, name is `USER_NAME`** |
| config_status (id, key, title) | Status name |
| ap_action_plan_type (id, title) | Type name |
| ap_action_plan_severity (id, title) | Severity / priority name |
| ap_action_plan_category (id, title) | Category name |
| ap_resolution_type (id, title) | Resolution type name |
| source_of_finding (id, title) | Source-of-finding name |

> Note: `config_user` uses uppercase `ID` and `USER_NAME` columns (not `id`/`title`).
