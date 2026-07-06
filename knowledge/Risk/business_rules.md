# Risk — Business Rules

## Status
`status_id` → `config_status.title`. Always join for the name.

## Ratings
- **Inherent rating**: `inherent_id` → `rcsa_assessmentdimensionscale.title` (e.g. High, Major,
  Extreme). The same table has a `color` column for the rating colour.
- **Residual rating**: `residual_id` → `rcsa_assessmentdimensionscale.title`.

## Category vs Type
- **Risk Category** = `riskcategory_id` → `config_riskcategory.title`.
- **Risk Type** = `risktype_id` → `config_rcsa_risktype.title`.

## Notes
- `r.description` may contain rich-text HTML — present as text.
- `key` is a reserved word in MySQL; always backtick it: `` r.`key` ``.
- Monthly trend grouping: `DATE_FORMAT(r.createdon, '%Y-%m')`.
