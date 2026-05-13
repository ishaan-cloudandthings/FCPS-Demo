# DATA_MODEL.md — FCPS Procurement Portal

> **Reference document.** Do not modify without explicit instruction and a corresponding ADR.
> All Oracle queries, Pydantic schemas, and API responses must conform to this model.

**Version:** 1.0
**Date:** May 2026
**Owner:** Cloud & Things (C&T)

---

## Table of Contents

1. [Design Decisions](#1-design-decisions)
2. [Entity Relationship Diagram](#2-entity-relationship-diagram)
3. [Enumerations](#3-enumerations)
4. [Entity Definitions](#4-entity-definitions)
5. [Indexes](#5-indexes)
6. [Constraints](#6-constraints)
7. [PII Classification](#7-pii-classification)
8. [Seed Data](#8-seed-data)

---

## 1. Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Oracle table naming | SCREAMING_SNAKE_CASE | Oracle convention |
| Role storage | STAFF.ROLE column | Oracle is the authoritative source for role; not sourced from ID.me |
| Procurement filter | STATUS column on PROCUREMENT_ITEMS | Simple flag-based RBAC filter at query level |
| Verification status | STAFF.IDME_VERIFIED column | Stored after successful ID.me callback; persists across sessions |
| Primary keys | NUMBER GENERATED ALWAYS AS IDENTITY | Standard Oracle auto-increment |
| Timestamps | TIMESTAMP WITH TIME ZONE | All timestamps UTC |

---

## 2. Entity Relationship Diagram

```
┌─────────────────────────────────────┐
│              STAFF                  │
│─────────────────────────────────────│
│ STAFF_ID (PK)                       │
│ EMPLOYEE_ID (UQ)     [PII]          │
│ FULL_NAME            [PII]          │
│ EMAIL                [PII]          │
│ DEPARTMENT                          │
│ JOB_TITLE                           │
│ PROCUREMENT_LEVEL (0–3)             │
│ ROLE (ADMIN | STAFF)                │
│ IDME_VERIFIED (Y | N)               │
│ ACTIVE (Y | N)                      │
│ CREATED_DATE                        │
│ UPDATED_DATE                        │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         PROCUREMENT_ITEMS           │
│─────────────────────────────────────│
│ ITEM_ID (PK)                        │
│ ITEM_NAME                           │
│ VENDOR_NAME                         │
│ CATEGORY                            │
│ STATUS (PENDING|APPROVED|REJECTED   │
│         |UNDER_REVIEW)              │
│ UNIT_PRICE                          │
│ CONTACT_NAME          [Admin only]  │
│ CONTACT_EMAIL         [Admin only]  │
│ BANK_DETAILS          [Admin only]  │
│ CREATED_DATE                        │
│ UPDATED_DATE                        │
└─────────────────────────────────────┘
```

---

## 3. Enumerations

### StaffRole

```
ADMIN   — Procurement coordinator. Sees all PROCUREMENT_ITEMS regardless of status.
STAFF   — Teacher / regular employee. Sees APPROVED items only.
```

### ProcurementLevel

```
0 — No procurement access. Access denied regardless of ID.me verification.
1 — Basic access. Minimum level for access granted.
2 — Standard access. Can view vendor contact details.
3 — Full access. Can view all fields including bank details.
```

### ProcurementStatus

```
PENDING      — Submitted, awaiting review. Visible to ADMIN only.
UNDER_REVIEW — Being assessed. Visible to ADMIN only.
APPROVED     — Cleared for procurement. Visible to ADMIN and STAFF.
REJECTED     — Not approved. Visible to ADMIN only.
```

---

## 4. Entity Definitions

### 4.1 STAFF

> ⚠️ **PII** — EMPLOYEE_ID, FULL_NAME, and EMAIL are PII. When writing any code that
> reads or returns these fields, AI must confirm data handling decisions with the human
> before generating. Applies in all zones.

| Column             | Type                      | Nullable | Notes                                      |
|--------------------|---------------------------|----------|--------------------------------------------|
| STAFF_ID           | NUMBER (PK, IDENTITY)     | NO       | Auto-increment primary key                 |
| EMPLOYEE_ID        | VARCHAR2(20)              | NO       | Unique. FCPS employee identifier. PII.     |
| FULL_NAME          | VARCHAR2(255)             | NO       | Legal full name. PII.                      |
| EMAIL              | VARCHAR2(255)             | NO       | Work email. Unique. PII.                   |
| DEPARTMENT         | VARCHAR2(100)             | NO       | e.g. Mathematics, Administration           |
| JOB_TITLE          | VARCHAR2(100)             | NO       | e.g. Teacher, Principal, Coordinator       |
| PROCUREMENT_LEVEL  | NUMBER(1)                 | NO       | 0–3. Controls access decision.             |
| ROLE               | VARCHAR2(10)              | NO       | ADMIN or STAFF.                            |
| IDME_VERIFIED      | CHAR(1)                   | NO       | Y or N. Updated after ID.me callback.      |
| ACTIVE             | CHAR(1)                   | NO       | Y or N. Inactive staff denied access.      |
| CREATED_DATE       | TIMESTAMP WITH TIME ZONE  | NO       | UTC. Set on insert.                        |
| UPDATED_DATE       | TIMESTAMP WITH TIME ZONE  | NO       | UTC. Updated on every write.               |

### 4.2 PROCUREMENT_ITEMS

> ⚠️ **PII** — CONTACT_NAME and CONTACT_EMAIL are PII. BANK_DETAILS is sensitive.
> AI must confirm data handling decisions before generating any code that reads or
> returns these fields.

| Column        | Type                      | Nullable | Notes                                           |
|---------------|---------------------------|----------|-------------------------------------------------|
| ITEM_ID       | NUMBER (PK, IDENTITY)     | NO       | Auto-increment primary key                      |
| ITEM_NAME     | VARCHAR2(255)             | NO       | Name of the procurement item or service         |
| VENDOR_NAME   | VARCHAR2(255)             | NO       | Supplying vendor name                           |
| CATEGORY      | VARCHAR2(100)             | NO       | e.g. Technology, Facilities, Supplies           |
| STATUS        | VARCHAR2(20)              | NO       | PENDING, UNDER_REVIEW, APPROVED, REJECTED       |
| UNIT_PRICE    | NUMBER(10,2)              | YES      | Unit price in USD                               |
| CONTACT_NAME  | VARCHAR2(255)             | YES      | Vendor contact. PII. Returned for Level 2+.     |
| CONTACT_EMAIL | VARCHAR2(255)             | YES      | Vendor contact email. PII. Returned for Level 2+|
| BANK_DETAILS  | VARCHAR2(500)             | YES      | Sensitive. Returned for Level 3 (Admin) only.   |
| CREATED_DATE  | TIMESTAMP WITH TIME ZONE  | NO       | UTC. Set on insert.                             |
| UPDATED_DATE  | TIMESTAMP WITH TIME ZONE  | NO       | UTC. Updated on every write.                    |

---

## 5. Indexes

| Table               | Index                        | Type         | Reason                               |
|---------------------|------------------------------|--------------|--------------------------------------|
| STAFF               | IDX_STAFF_EMPLOYEE_ID        | UNIQUE BTREE | Lookup by employee ID post-ID.me     |
| STAFF               | IDX_STAFF_EMAIL              | UNIQUE BTREE | Lookup by email                      |
| STAFF               | IDX_STAFF_ROLE               | BTREE        | Filter Admin vs Staff                |
| PROCUREMENT_ITEMS   | IDX_PROC_STATUS              | BTREE        | RBAC filter on status                |
| PROCUREMENT_ITEMS   | IDX_PROC_CATEGORY            | BTREE        | Category filter on list views        |

---

## 6. Constraints

| Table             | Constraint              | Rule                                                  |
|-------------------|-------------------------|-------------------------------------------------------|
| STAFF             | CHK_ROLE                | ROLE IN ('ADMIN', 'STAFF')                            |
| STAFF             | CHK_PROC_LEVEL          | PROCUREMENT_LEVEL BETWEEN 0 AND 3                     |
| STAFF             | CHK_VERIFIED            | IDME_VERIFIED IN ('Y', 'N')                           |
| STAFF             | CHK_ACTIVE              | ACTIVE IN ('Y', 'N')                                  |
| PROCUREMENT_ITEMS | CHK_STATUS              | STATUS IN ('PENDING', 'UNDER_REVIEW', 'APPROVED', 'REJECTED') |
| PROCUREMENT_ITEMS | CHK_PRICE               | UNIT_PRICE > 0 OR UNIT_PRICE IS NULL                  |

---

## 7. PII Classification

| Table             | Column         | PII Type              | Protection Rule                                  |
|-------------------|----------------|-----------------------|--------------------------------------------------|
| STAFF             | EMPLOYEE_ID    | Identifier            | Never logged. Not in list responses.             |
| STAFF             | FULL_NAME      | Personal identity     | Never logged. Scoped to owning user.             |
| STAFF             | EMAIL          | Contact identifier    | Never logged. Not in list responses.             |
| PROCUREMENT_ITEMS | CONTACT_NAME   | Personal identity     | Returned for PROCUREMENT_LEVEL >= 2 only.        |
| PROCUREMENT_ITEMS | CONTACT_EMAIL  | Contact identifier    | Returned for PROCUREMENT_LEVEL >= 2 only.        |
| PROCUREMENT_ITEMS | BANK_DETAILS   | Financial (sensitive) | Returned for PROCUREMENT_LEVEL = 3 (Admin) only. |

---

## 8. Seed Data

### STAFF (10 records)

| EMPLOYEE_ID | FULL_NAME           | DEPARTMENT      | JOB_TITLE              | LEVEL | ROLE  |
|-------------|---------------------|-----------------|------------------------|-------|-------|
| FCPS-001    | Sarah Mitchell      | Administration  | Procurement Coordinator| 3     | ADMIN |
| FCPS-002    | James Okafor        | Administration  | Procurement Coordinator| 3     | ADMIN |
| FCPS-003    | Linda Nguyen        | Mathematics     | Teacher                | 1     | STAFF |
| FCPS-004    | Marcus Thompson     | Science         | Teacher                | 1     | STAFF |
| FCPS-005    | Priya Patel         | English         | Teacher                | 1     | STAFF |
| FCPS-006    | David Hernandez     | IT              | Systems Administrator  | 2     | STAFF |
| FCPS-007    | Amara Johnson       | Facilities      | Facilities Manager     | 2     | STAFF |
| FCPS-008    | Robert Kim          | Arts            | Teacher                | 1     | STAFF |
| FCPS-009    | Fatima Al-Hassan    | Special Ed      | Teacher                | 1     | STAFF |
| FCPS-010    | Christopher Evans   | PE              | Teacher                | 0     | STAFF |

> FCPS-010 has PROCUREMENT_LEVEL = 0 — use this record to demo the access denied scenario.

### PROCUREMENT_ITEMS (15 records across all statuses)

5 APPROVED — visible to Admin and Staff
4 PENDING — visible to Admin only
3 UNDER_REVIEW — visible to Admin only
3 REJECTED — visible to Admin only

Categories: Technology, Facilities, Supplies, Services, Furniture
