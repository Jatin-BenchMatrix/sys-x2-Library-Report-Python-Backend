# Action Plan — Relationships & Joins

All joins are from `ap_actionplan ap`. Use LEFT JOIN (FKs can be NULL).

```sql
LEFT JOIN config_businesshierarchy bh ON bh.id  = ap.business_hierarchy_id   -- Department
LEFT JOIN config_user              ow ON ow.ID  = ap.assigned_to_id          -- Owner
LEFT JOIN config_user              rp ON rp.ID  = ap.responsible_person      -- Responsible person
LEFT JOIN config_status            st ON st.id  = ap.status_id               -- Status
LEFT JOIN ap_action_plan_type      tp ON tp.id  = ap.action_plan_type_id     -- Type
LEFT JOIN ap_action_plan_severity  sv ON sv.id  = ap.action_plan_severity_id -- Severity / priority
LEFT JOIN ap_action_plan_category  ct ON ct.id  = ap.action_plan_category_id -- Category
LEFT JOIN ap_resolution_type       rt ON rt.id  = ap.resolution_type_id      -- Resolution type
LEFT JOIN source_of_finding        sf ON sf.id  = ap.source_of_finding_id    -- Source of finding
```

Display columns to select from the joins:
- Department  → `bh.title`
- Owner       → `ow.USER_NAME`
- Responsible → `rp.USER_NAME`
- Status      → `st.title`
- Type        → `tp.title`
- Severity    → `sv.title`
- Category    → `ct.title`
- Resolution  → `rt.title`
- Source      → `sf.title`
