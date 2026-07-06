# Risk — Common Charts, Filters & Example Prompts

## Common filters
- Department: `r.businesshierarchy_id` (show `bh.title`)
- Risk Category: `r.riskcategory_id` (show `rc.title`)
- Risk Type: `r.risktype_id`
- Status: `r.status_id`

## Common charts
- Count by Risk Category, Count by Department, Count by Inherent rating, Count by Residual rating.

## Example prompts → SQL

### "Bar chart of risks by category"
```sql
SELECT rc.title AS label, COUNT(*) AS value
FROM rcsa_risk r
LEFT JOIN config_riskcategory rc ON rc.id = r.riskcategory_id
GROUP BY rc.title
ORDER BY value DESC
```

### "Pie chart of risks by inherent rating"
```sql
SELECT ia.title AS label, COUNT(*) AS value
FROM rcsa_risk r
LEFT JOIN rcsa_assessmentdimensionscale ia ON ia.id = r.inherent_id
GROUP BY ia.title
ORDER BY value DESC
```

### "KPI of total risks"
```sql
SELECT COUNT(*) AS value FROM rcsa_risk r
```

### "List risks: Reference, Title, Category, Department, Inherent, Residual"
```sql
SELECT r.`key` AS `Reference`, r.title AS `Title`, rc.title AS `Risk Category`,
       bh.title AS `Department`, ia.title AS `Inherent`, ra.title AS `Residual`
FROM rcsa_risk r
LEFT JOIN config_riskcategory           rc ON rc.id = r.riskcategory_id
LEFT JOIN config_businesshierarchy      bh ON bh.id = r.businesshierarchy_id
LEFT JOIN rcsa_assessmentdimensionscale ia ON ia.id = r.inherent_id
LEFT JOIN rcsa_assessmentdimensionscale ra ON ra.id = r.residual_id
ORDER BY r.id
```
