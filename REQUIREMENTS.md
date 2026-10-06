# Hair Purchasing Management System

## 1. Project Overview

This project implements a **Hair Purchasing Management System** using **Odoo 20.0 Community Edition**.

The system manages the complete lifecycle of purchasing human hair from individual sellers, collectors, or agents, including:

- Seller management
- Hair intake
- Weight measurement
- Hair classification
- Quality grading
- Automatic pricing
- Purchase confirmation
- Payment tracking
- Inventory receipt
- Lot/batch traceability
- Hair processing
- Processing loss and yield tracking
- Reporting and dashboards
- Audit trails

The system must use standard Odoo functionality wherever practical and extend Odoo through custom modules where hair-specific business logic is required.

---

# 2. Primary Business Flow

The primary workflow is:

Seller / Collector  
→ Hair Intake  
→ Weight Measurement  
→ Classification  
→ Quality Inspection  
→ Grade Assignment  
→ Automatic Pricing  
→ Purchase Confirmation  
→ Payment  
→ Inventory Receipt  
→ Lot / Batch Tracking  
→ Processing  
→ Finished Hair Stock

Every confirmed purchase must remain traceable from the original seller through inventory and subsequent processing.

---

# 3. Project Goals

The system must:

1. Standardize the hair purchasing process.
2. Reduce manual price calculations.
3. Prevent unauthorized price manipulation.
4. Maintain accurate purchased weights.
5. Track purchased hair by lot/batch.
6. Maintain seller purchase history.
7. Support multiple hair grades, types, and lengths.
8. Support configurable pricing rules.
9. Track purchase payments.
10. Track processing losses and yields.
11. Provide management reporting.
12. Maintain an audit trail for important business operations.
13. Support future multi-branch operations.
14. Preserve historical business data when configuration changes.

---

# 4. Users and Roles

The system must support at least the following roles.

## 4.1 Hair Buyer

Can:

- Create purchase intake records
- Select/create sellers where permitted
- Record hair characteristics
- Record weights
- Submit purchases for confirmation

Cannot:

- Override protected prices
- Cancel confirmed purchases
- Modify confirmed financial information unless explicitly permitted

## 4.2 Quality Officer

Can:

- Inspect hair
- Record quality criteria
- Assign or approve grades
- Record rejection reasons
- Attach inspection evidence

## 4.3 Cashier

Can:

- View confirmed payable purchases
- Record seller payments
- Select payment method
- Print payment/purchase receipts

Cannot:

- Modify grading or purchase quantities

## 4.4 Warehouse User

Can:

- Receive purchased hair
- Manage hair lots/batches
- Perform permitted stock operations

## 4.5 Branch Manager

Can:

- Review branch purchases
- Approve permitted overrides
- Cancel purchases according to policy
- Access branch reports
- Review audit information

## 4.6 Accountant

Can:

- Review financial transactions
- Manage accounting-related operations
- Reconcile purchase payments where accounting integration is enabled

## 4.7 Administrator

Can configure and administer the complete system.

Access rights must use Odoo groups, ACLs, and record rules.

---

# 5. Seller Management

Use or extend `res.partner` instead of creating an isolated duplicate contact system unless implementation constraints require otherwise.

A seller may represent:

- Individual Seller
- Collector
- Agent

Seller information should support:

- Name
- Phone
- Alternative phone
- Seller type
- Identification/NRC where required
- Address
- Township/region
- Notes
- Active/inactive status
- Purchase history

The system should provide derived statistics such as:

- Number of purchases
- Total purchased weight
- Total purchase value
- Last purchase date

Sensitive seller information must only be visible to authorized users.

---

# 6. Hair Master Data

The system must provide configurable master data.

## 6.1 Hair Type

Examples:

- Virgin Hair
- Remy Hair
- Non-Remy Hair
- Processed Hair

Values must be configurable and must not be hard-coded into business logic.

## 6.2 Hair Texture

Examples:

- Straight
- Wavy
- Curly

## 6.3 Hair Color

Hair colors must be configurable.

## 6.4 Hair Grade

Examples:

- Grade A
- Grade B
- Grade C
- Rejected

Grades must be configurable.

## 6.5 Hair Length

The system must support hair length measurement, normally in inches.

Pricing rules must be capable of using either:

- Exact lengths
- Length ranges

Example:

10–14 inches  
15–18 inches  
19–22 inches  
23–26 inches  
27+ inches

Ranges must not overlap when they are active for the same pricing context.

---

# 7. Purchase Intake

A hair purchase must have a unique Odoo sequence.

Example:

`HP/2026/00001`

A purchase should contain:

- Reference
- Purchase date/time
- Company
- Branch, when branch functionality is enabled
- Buyer
- Seller
- Currency
- Hair details
- Weight information
- Grade
- Pricing information
- Payment information
- Attachments/photos
- Notes
- Status

The exact model structure may use purchase headers and purchase lines if multiple classifications are required within one seller transaction.

The implementation must prefer a design capable of supporting multiple hair lines per purchase without breaking historical records.

---

# 8. Weight Management

The system must distinguish between measured and payable weight.

Supported values should include:

- Gross Weight
- Packaging/Tare Weight
- Waste Weight
- Moisture Deduction where applicable
- Other approved deductions
- Net/Payable Weight

A typical calculation is:

Net Weight = Gross Weight  
− Tare Weight  
− Waste Weight  
− Moisture Deduction  
− Other Weight Deductions

Negative net weight must never be allowed.

Weight values must use appropriate decimal precision.

The initial system may support manual weight entry.

The architecture should allow future integration with digital weighing scales without redesigning the purchasing model.

---

# 9. Quality Inspection

Quality inspection should support configurable criteria such as:

- Hair type
- Natural/processed condition
- Dyed/not dyed
- Texture
- Thickness
- Damage
- Gray hair percentage
- Mixed hair percentage
- Moisture
- Waste percentage
- Length
- General condition

The final inspection must result in:

- Grade
- Accepted/rejected decision
- Inspector
- Inspection date/time

Inspection photos or supporting attachments should be allowed.

Rejected purchases must require a reason.

Quality criteria must remain extensible.

---

# 10. Pricing Engine

Pricing must be configuration-driven.

Prices must never be permanently hard-coded into Python or JavaScript.

Pricing should be capable of considering:

- Hair type
- Hair grade
- Length or length range
- Branch
- Company
- Effective date
- Currency
- Unit of measure

A basic pricing matrix may resemble:

| Length | Grade A | Grade B | Grade C |
|---|---:|---:|---:|
| 10–14" | 500/g | 400/g | 300/g |
| 15–18" | 700/g | 550/g | 400/g |
| 19–22" | 900/g | 700/g | 500/g |
| 23–26" | 1,200/g | 900/g | 650/g |
| 27"+ | 1,500/g | 1,100/g | 800/g |

The actual values are configuration data and not fixed requirements.

---

# 11. Price Calculation

The standard calculation is:

Purchase Amount = Payable Weight × Unit Price

Example:

Payable Weight = 600 g  
Unit Price = 1,200 MMK/g

Purchase Amount = 720,000 MMK

The selected pricing rule must be stored or otherwise historically traceable.

Changing a pricing configuration later must **not** silently modify previously confirmed purchases.

Confirmed purchases must retain the actual unit price and amount used at confirmation time.

---

# 12. Price Override

Price overrides must be restricted.

Authorized users may override the automatically calculated rate when business policy permits.

An override must record:

- Original rate
- New rate
- User
- Date/time
- Reason

A reason is mandatory.

Unauthorized users must not be able to bypass the restriction through UI, RPC, import, or direct model calls.

---

# 13. Purchase States

The initial purchase lifecycle should support:

`Draft → Inspection → Confirmed → Paid → Received`

Additional terminal states:

- Rejected
- Cancelled

Exact technical states may be refined during implementation.

State transitions must enforce business rules.

Examples:

A rejected purchase cannot be paid.

A cancelled purchase cannot create new stock movements.

A purchase cannot become `Confirmed` without required seller, weight, grade, and pricing information.

A purchase must not become `Paid` unless it has been confirmed.

---

# 14. Confirmation

Confirmation represents acceptance of the commercial purchase.

When confirmed, important values must be protected, including:

- Seller
- Hair classification
- Weight
- Grade
- Unit price
- Total amount

Changing protected values after confirmation must either:

1. Be prohibited, or
2. Require an explicit authorized correction workflow with audit history.

The system must never silently rewrite confirmed historical transactions.

---

# 15. Payment

The system must support payment statuses:

- Unpaid
- Partially Paid
- Paid

Payment methods should be configurable.

Initial examples:

- Cash
- Bank Transfer
- KBZPay
- WavePay
- Other

Do not hard-code payment providers into core business logic.

A payment record should preserve:

- Purchase
- Seller
- Amount
- Payment date
- Payment method
- Reference
- User
- Notes

The design should support partial payments even if the initial UI primarily uses full payment.

---

# 16. Accounting Integration

Where Odoo Accounting is installed/configured, the system should integrate with standard Odoo accounting models rather than implementing a separate accounting ledger.

Hair-specific modules must not duplicate Odoo accounting functionality unnecessarily.

Accounting integration must be isolated enough that the core purchasing workflow remains maintainable.

---

# 17. Inventory Receipt

Confirmed/accepted hair must be receivable into Odoo Inventory.

The system should use standard Odoo stock models wherever possible.

Purchased hair must retain traceability to:

- Purchase
- Seller
- Hair characteristics
- Grade
- Original purchased weight

---

# 18. Lot / Batch Tracking

Purchased hair should support lot/batch tracking.

Example:

`HAIR/2026/00001`

A lot should be traceable to its source purchase.

Relevant information may include:

- Purchase
- Seller
- Purchase date
- Original weight
- Hair type
- Grade
- Length
- Source/origin
- Current quantity
- Processing history

Do not duplicate information unnecessarily when it can safely be obtained through relationships.

Historical traceability must not depend on mutable seller or pricing configuration alone.

---

# 19. Processing

The system should support processing raw hair into processed/finished hair.

Example:

Raw Hair  
→ Sorting  
→ Washing  
→ Drying  
→ Processing  
→ Grading  
→ Bundling  
→ Finished Hair

Where practical, processing should build on Odoo Manufacturing and Inventory rather than creating a separate stock engine.

---

# 20. Processing Yield

The system must be capable of tracking:

- Input weight
- Output weight
- Loss weight
- Yield percentage

Example:

Input = 1,000 g  
Output = 880 g

Loss = 120 g

Yield = 88%

Yield formula:

`Yield % = Output Weight / Input Weight × 100`

Processing output must remain traceable to its input lots.

---

# 21. Multi-Company and Branch Readiness

All business transaction models must be designed with Odoo multi-company rules in mind.

Relevant models should use `company_id`.

Branch-specific functionality may be custom if Odoo Community does not provide the required business concept directly.

The design must allow:

Company  
→ Branch  
→ Buyer / Cashier / Warehouse

Users should only access companies/branches permitted by their security configuration.

---

# 22. Audit Trail

Important operations must be auditable.

At minimum, audit requirements apply to:

- Price overrides
- Weight corrections after confirmation
- Grade changes after approval
- Purchase cancellation
- Payment cancellation/reversal
- Other protected confirmed-data corrections

Audit information should capture:

- User
- Date/time
- Operation
- Previous value where relevant
- New value where relevant
- Reason

Use Odoo chatter/tracking where suitable and introduce custom audit records only where standard tracking is insufficient.

---

# 23. Attachments and Photos

Users should be able to attach supporting evidence to purchases and inspections.

Examples:

- Hair photo
- Weight-scale photo
- Seller evidence
- Quality inspection photo

Use Odoo's standard attachment infrastructure.

Do not store raw binary files in custom database fields without a justified requirement.

---

# 24. Search and Filtering

Users should be able to search/filter purchases by relevant dimensions, including:

- Reference
- Seller
- Phone
- Date
- Buyer
- Branch
- Grade
- Hair type
- Status
- Payment status
- Lot

Useful group-by options should be provided.

---

# 25. Dashboard and Reporting

Management reporting should eventually provide KPIs such as:

- Total purchased weight
- Total purchase value
- Number of purchases
- Number of sellers
- Average price per weight unit
- Purchases by grade
- Purchases by hair type
- Purchases by length
- Purchases by branch
- Purchases by buyer
- Purchases by seller
- Processing loss
- Processing yield

Reports should support useful periods such as:

- Today
- Yesterday
- This week
- This month
- Custom range

Dashboard implementation must not compromise transactional model performance.

---

# 26. Documents / Receipts

The system should provide a printable purchase receipt.

The receipt should include relevant information such as:

- Purchase reference
- Date
- Seller
- Hair description
- Weight
- Grade
- Unit price
- Total
- Payment information where appropriate

Report templates must use Odoo QWeb.

---

# 27. Data Integrity

The implementation must enforce business integrity at the server/model layer.

Do not rely only on frontend validation.

Important constraints include:

- Weight cannot be negative.
- Payable weight cannot exceed logically valid measured weight.
- Purchase amount cannot be negative.
- Required pricing information must exist before confirmation.
- Required grading information must exist before confirmation.
- Rejected purchases cannot be paid.
- Cancelled purchases cannot create additional stock.
- Invalid state transitions must be blocked.
- Cross-company data leakage must be prevented.

Use:

- SQL constraints where appropriate
- Python constraints
- ORM validation
- Access controls
- Record rules

---

# 28. Concurrency and Idempotency

Critical actions must avoid accidental duplicate processing.

Examples include:

- Purchase confirmation
- Inventory receipt creation
- Payment creation
- Processing completion

Repeated button calls or RPC retries must not create duplicate stock or financial transactions.

---

# 29. Security Requirements

Security must be implemented from the beginning, not added only at the end.

Every custom business model must have appropriate:

- Access control entries
- Security groups
- Record rules where necessary
- Multi-company protection

Public or portal access must not be introduced unless explicitly required.

Sensitive seller identification information must be restricted.

---

# 30. Technical Requirements

Platform:

- Odoo 20.0 Community
- PostgreSQL
- Python version supported by Odoo 20
- Docker-based development environment

Development requirements:

- Do not modify Odoo core.
- Custom functionality belongs in custom addons.
- Prefer Odoo ORM.
- Raw SQL requires a documented justification.
- Follow Odoo naming conventions.
- Follow Odoo 20 API patterns.
- Avoid deprecated APIs.
- Avoid unnecessary dependencies.
- Keep modules independently maintainable.
- Avoid circular module dependencies.

---

# 31. Initial Module Boundaries

Initial target modules:

### `hair_base`

Responsible for:

- Hair types
- Hair grades
- Hair lengths/ranges
- Hair textures
- Hair colors
- Shared configuration
- Shared security concepts where appropriate

### `hair_supplier`

Responsible for:

- Seller extensions
- Seller types
- Seller purchase information

Depends on:

`hair_base`

### `hair_purchase`

Responsible for:

- Purchase intake
- Weight calculations
- Quality/grading workflow
- Pricing
- Purchase confirmation
- Purchase receipt/report

Depends on:

`hair_base`  
`hair_supplier`

### `hair_inventory`

Responsible for:

- Inventory integration
- Hair lots
- Purchase-to-stock traceability

Depends on:

`hair_purchase`  
`stock`

### `hair_processing`

Responsible for:

- Processing workflow
- Input/output traceability
- Loss
- Yield

Depends on:

`hair_inventory`

Use Odoo Manufacturing when appropriate.

### `hair_dashboard`

Responsible for:

- Management KPIs
- Analytical views
- Reporting/dashboard functionality

Depends on relevant transactional modules.

Module boundaries may be refined in `ARCHITECTURE.md`, but changes must preserve clear responsibilities and avoid circular dependencies.

---

# 32. Testing Requirements

Every business-critical feature must have automated tests.

Tests must cover at least:

### Weight

- Correct net weight calculation
- Invalid negative values
- Excessive deductions

### Pricing

- Correct pricing rule selection
- Effective-date behavior
- Grade-based pricing
- Length-based pricing
- No matching price rule
- Price override permissions

### Purchase

- Valid confirmation
- Missing required data
- Invalid state transitions
- Rejection
- Cancellation

### Payment

- Full payment
- Partial payment
- Invalid payment amount
- Rejected purchase payment prevention
