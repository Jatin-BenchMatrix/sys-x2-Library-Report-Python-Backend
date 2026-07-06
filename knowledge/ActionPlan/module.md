# Module: Action Plan

## Description
The Action Plan module tracks remediation actions / corrective tasks raised across the
GRC platform (from risks, controls, incidents, audits). Each action plan has an owner,
a department, a due date, a severity, a type/category, and a workflow status.

## Purpose
Track what needs to be done, by whom, by when, and whether it is on track, overdue, or
closed — so management can monitor remediation progress.

## Business meaning
- An **Action Plan** is a single corrective action / task.
- It is **assigned** to a user (owner), belongs to a **department** (business hierarchy),
  and has a **target/expected completion date**.
- Its lifecycle is driven by a **status** and tracked against its dates.

## Main entity
`ap_actionplan` (alias suggestion: `ap`)
