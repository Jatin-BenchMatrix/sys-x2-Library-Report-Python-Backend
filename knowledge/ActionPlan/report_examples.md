# Action Plan — Common Charts, Filters & Example Prompts

## Common filters
- Department: `ap.business_hierarchy_id` (show `bh.title`)
- Owner: `ap.assigned_to_id` (show `ow.USER_NAME`)
- Status: `ap.status_id` (show `st.title`)
- Severity/Priority: `ap.action_plan_severity_id` (show `sv.title`)
- Date range: `ap.expected_completion_date` / `ap.created_on`

## Common charts
- **Count by Status**, **Count by Department**, **Priority distribution**, **Open vs Closed**, **Monthly trend**.

## Example prompts → SQL

### "Bar chart of open action plans by department"
```sql
SELECT bh.title AS label, COUNT(*) AS value
FROM ap_actionplan ap
LEFT JOIN config_businesshierarchy bh ON bh.id = ap.business_hierarchy_id
WHERE ap.actual_completion_date IS NULL
GROUP BY bh.title
ORDER BY value DESC
```

### "KPI of total open actions"
```sql
SELECT COUNT(*) AS value
FROM ap_actionplan ap
WHERE ap.actual_completion_date IS NULL
```

### "Pie chart of action plans by priority"
```sql
SELECT sv.title AS label, COUNT(*) AS value
FROM ap_actionplan ap
LEFT JOIN ap_action_plan_severity sv ON sv.id = ap.action_plan_severity_id
GROUP BY sv.title
ORDER BY value DESC
```

### "Monthly trend of created action plans"
```sql
SELECT DATE_FORMAT(ap.created_on, '%Y-%m') AS label, COUNT(*) AS value
FROM ap_actionplan ap
GROUP BY DATE_FORMAT(ap.created_on, '%Y-%m')
ORDER BY label
```

### "List overdue actions: Reference, Title, Owner, Due Date, Status"
```sql
SELECT ap.ref_key AS `Reference`, ap.title AS `Title`, ow.USER_NAME AS `Owner`,
       DATE_FORMAT(ap.expected_completion_date, '%d %b, %Y') AS `Due Date`, st.title AS `Status`
FROM ap_actionplan ap
LEFT JOIN config_user   ow ON ow.ID = ap.assigned_to_id
LEFT JOIN config_status st ON st.id = ap.status_id
WHERE ap.expected_completion_date < CURDATE() AND ap.actual_completion_date IS NULL
ORDER BY ap.expected_completion_date
```
