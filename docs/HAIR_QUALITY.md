# Quality Inspection and Grade Approval

The hair_purchase module provides Draft → Inspection and terminal Rejected states.
Commercial confirmation, payments and stock receipt remain separate features.

## Buyer workflow

Record seller and hair lines, then Submit for Inspection. Every line needs a
hair type, length and positive payable kg. Repeated submit calls do not duplicate
an inspection. Weights, classification, seller/date/buyer/company and line
membership are locked once submitted.

Use Return to Draft to correct an intake under inspection. Reopening an approved
inspection requires a reason. It clears grades, approval and inspector/date,
requiring fresh inspection after changes. Chatter retains previous approved
grades and the reason. Rejected intakes cannot reopen through this action.
Duplicating an intake creates a fresh draft without copied approval/inspection
provenance or grades.

## Quality Officer workflow

Assign Inspection Grade to every line on the Quality tab. Approve Quality records
approved grades, inspector and timestamp; repeated approval retains the original
provenance. Approval leaves the intake in Inspection awaiting commercial review.
Approved findings cannot be edited without returning to draft.

To reject, enter a nonblank rejection reason and press Reject. Rejection records
inspector/time and makes the intake terminal. Notes and standard chatter
attachments support inspection evidence. Type/length/grade are the initial
required classification dimensions; additional criterion configuration remains
future work. No arbitrary damage, moisture or waste thresholds are introduced.

## Security and audit

Quality Officer is a separate Odoo privilege. It grants company-scoped read/update
of intakes and lines, plus master-data read access. It does not grant Buyer seller
create/edit permissions or Manager NRC access. Administrators inherit the quality
role. Buyers cannot assign/approve grades or record inspection findings.

Protected states, approved grades and provenance cannot be written through ORM,
RPC, import or forged context defaults. Public actions check role and record access
before mutation. Odoo's ORM row locks serialize actions and input edits; no raw
SQL or sudo bypass is used. State/approval/provenance tracking and grade/revision
messages retain the audit trail in chatter.

Eight automated tests cover submission validation/retries, approval/reset/copy,
role separation and NRC access, frozen inputs/membership, mandatory rejection
reasons, direct/context forgery, company integrity, approved findings and views.
