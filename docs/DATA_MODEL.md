# DATA_MODEL.md — Staff Procurement Portal

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
│ ROLE                                │
│  (PROCUREMENT_SUPERVISOR            │
│   | REGULAR_STAFF | NON_STAFF)      │
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

Per [ADR-015](adr/ADR-015-role-model-simplification.md):

```
PROCUREMENT_SUPERVISOR — Procurement coordinator. Sees all PROCUREMENT_ITEMS
                        regardless of status. Holds documented authority to
                        add / update / delete vendor records (CRUD endpoints
                        are a future story per ADR-015).
REGULAR_STAFF          — Teacher / general employee. Read access; sees
                        APPROVED vendors only.
NON_STAFF              — Person exists in STAFF but has no portal access.
                        Denied at /api/auth/callback with
                        `X-Auth-Reason: NON_STAFF`.
```

### ProcurementStatus

```
PENDING      — Submitted, awaiting review. Visible to PROCUREMENT_SUPERVISOR only.
UNDER_REVIEW — Being assessed. Visible to PROCUREMENT_SUPERVISOR only.
APPROVED     — Cleared for procurement. Visible to PROCUREMENT_SUPERVISOR and REGULAR_STAFF.
REJECTED     — Not approved. Visible to PROCUREMENT_SUPERVISOR only.
```

---

## 4. Entity Definitions

### 4.1 STAFF

> ⚠️ **PII** — EMPLOYEE_ID, FULL_NAME, and EMAIL are PII. When writing any code that
> reads or returns these fields, AI must confirm data handling decisions with the human
> before generating. Applies in all zones.

> Per [ADR-015](adr/ADR-015-role-model-simplification.md) (2026-05-19):
> `PROCUREMENT_LEVEL` is **removed**; `ROLE` is the single authority
> field with three values (`PROCUREMENT_SUPERVISOR`, `REGULAR_STAFF`,
> `NON_STAFF`).

| Column             | Type                      | Nullable | Notes                                      |
|--------------------|---------------------------|----------|--------------------------------------------|
| STAFF_ID           | NUMBER (PK, IDENTITY)     | NO       | Auto-increment primary key                 |
| EMPLOYEE_ID        | VARCHAR2(20)              | NO       | Unique. employee identifier. PII.     |
| FULL_NAME          | VARCHAR2(255)             | NO       | Legal full name. PII.                      |
| EMAIL              | VARCHAR2(255)             | NO       | Work email. Unique. PII.                   |
| DEPARTMENT         | VARCHAR2(100)             | NO       | e.g. Mathematics, Administration           |
| JOB_TITLE          | VARCHAR2(100)             | NO       | e.g. Teacher, Principal, Coordinator       |
| ROLE               | VARCHAR2(25)              | NO       | `PROCUREMENT_SUPERVISOR`, `REGULAR_STAFF`, or `NON_STAFF` (ADR-015). |
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
| STAFF             | CHK_ROLE                | ROLE IN ('PROCUREMENT_SUPERVISOR', 'REGULAR_STAFF', 'NON_STAFF') |
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
| PROCUREMENT_ITEMS | CONTACT_NAME   | Personal identity     | Returned to authenticated readers (today every authenticated session). Future per-role narrowing tracked in ADR-015 follow-ups. |
| PROCUREMENT_ITEMS | CONTACT_EMAIL  | Contact identifier    | Detail-only per ADR-013 — only `GET /api/vendors/{id}` returns it. |
| PROCUREMENT_ITEMS | BANK_DETAILS   | Financial (sensitive) | Out of scope entirely per ADR-012 — column removed. |

---

## 8. Seed Data

### STAFF (10 records)

| EMPLOYEE_ID | FULL_NAME           | DEPARTMENT      | JOB_TITLE              | ROLE                     |
|-------------|---------------------|-----------------|------------------------|--------------------------|
| EMP-001     | Sarah Mitchell      | Administration  | Procurement Coordinator| PROCUREMENT_SUPERVISOR   |
| EMP-002     | James Okafor        | Administration  | Procurement Coordinator| PROCUREMENT_SUPERVISOR   |
| EMP-003     | Linda Nguyen        | Mathematics     | Teacher                | REGULAR_STAFF            |
| EMP-004     | Marcus Thompson     | Science         | Teacher                | REGULAR_STAFF            |
| EMP-005     | Priya Patel         | English         | Teacher                | REGULAR_STAFF            |
| EMP-006     | David Hernandez     | IT              | Systems Administrator  | REGULAR_STAFF            |
| EMP-007     | Amara Johnson       | Facilities      | Facilities Manager     | REGULAR_STAFF            |
| EMP-008     | Robert Kim          | Arts            | Teacher                | REGULAR_STAFF            |
| EMP-009     | Fatima Al-Hassan    | Special Ed      | Teacher                | REGULAR_STAFF            |
| EMP-010     | Christopher Evans   | PE              | Teacher                | NON_STAFF                |

> EMP-010 has `ROLE = 'NON_STAFF'` — use this record to demo the access denied scenario.

### PROCUREMENT_ITEMS (15 records across all statuses)

5 APPROVED — visible to Regular Staff and Procurement Supervisor
4 PENDING — visible to Procurement Supervisor only
3 UNDER_REVIEW — visible to Procurement Supervisor only
3 REJECTED — visible to Procurement Supervisor only

Categories: Technology, Facilities, Supplies, Services, Furniture
