# Action Plan — Business Rules

## Status
`status_id` → `config_status.title` is the workflow status (e.g. Open, In Progress,
Closed). Always join `config_status` to show the name; never hardcode status ids.

## Severity / Priority
`action_plan_severity_id` → `ap_action_plan_severity.title` is the priority
(e.g. High / Medium / Low). "Priority" and "Severity" mean the same field here.

## Open vs Closed (derived)
- **Open / not completed**: `ap.actual_completion_date IS NULL` (and `ap.closure_date IS NULL`).
- **Closed / completed**: `ap.actual_completion_date IS NOT NULL` OR `ap.closure_date IS NOT NULL`.

## Overdue (derived)
An action is **overdue** when it is not yet completed and its due date has passed:
```sql
ap.expected_completion_date < CURDATE()
AND ap.actual_completion_date IS NULL
```

## Business calculations
- **Average closure time (days)**: `AVG(DATEDIFF(ap.actual_completion_date, ap.start_date))`
  over completed actions (`actual_completion_date IS NOT NULL`).
- **Open count**: `COUNT(*)` where open (see above).
- **On time**: `actual_completion_date <= expected_completion_date`.

## Dates
- Due date = `expected_completion_date`.
- Use `DATE_FORMAT(<col>, '%d %b, %Y')` to format dates for display/listings.
- Monthly trend grouping: `DATE_FORMAT(ap.created_on, '%Y-%m')`.
