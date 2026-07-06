# Risk — Relationships & Joins

From `rcsa_risk r`, use LEFT JOIN:

```sql
LEFT JOIN config_businesshierarchy      bh ON bh.id = r.businesshierarchy_id   -- Department
LEFT JOIN config_riskcategory           rc ON rc.id = r.riskcategory_id         -- Risk Category
LEFT JOIN config_rcsa_risktype          rt ON rt.id = r.risktype_id             -- Risk Type
LEFT JOIN config_status                 st ON st.id = r.status_id               -- Status
LEFT JOIN rcsa_assessmentdimensionscale ia ON ia.id = r.inherent_id            -- Inherent rating
LEFT JOIN rcsa_assessmentdimensionscale ra ON ra.id = r.residual_id            -- Residual rating
```

Display columns:
- Department → `bh.title`
- Risk Category → `rc.title`
- Risk Type → `rt.title`
- Status → `st.title`
- Inherent → `ia.title`
- Residual → `ra.title`
- Reference → `` r.`key` `` ; Title → `r.title`
