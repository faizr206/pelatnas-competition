# UI Guidelines for Competition Platform

This document defines the UI/UX structure inspired by:

* TLX (competitive programming dashboard style)
* Kaggle (competition detail experience)

Current implementation note:

* The current web app already implements `/`, `/competitions`, `/competitions/[slug]`, and `/login`
* Use this file together with `CURRENT_IMPLEMENTATION_GUIDE.md` when changing UI behavior

---

# 1. Overall UX Philosophy

* **Homepage = simple, lightweight, TLX-style**
* **Competition page = rich, Kaggle-style workspace**
* Minimize friction for first-time users
* Gradually increase complexity as users engage

---

# 2. First-Time User Experience (Landing / Home)

## Goal

Make it feel simple and not overwhelming.

## Layout (TLX-inspired)

### Top Navigation

* Logo (left)
* Navigation:

  * Home
  * Competitions
  * More
* User profile (right)

Current MVP rule:

* Keep the shared header height visually identical across landing, competition, and login-adjacent flows that use the shared header
* Prefer a shared header component over page-specific navbar copies

---

## Main Content

### Section: Active Competitions

Display as cards or simple list:

Each competition shows:

* Title
* Short description
* Status (Active / Upcoming / Finished)
* "View" button

Example:

```text
[ CreditSense: Loan Risk Assessment ]
  Active · 21 days left
  "Predict loan risk tier"
  [ View Competition ]
```

---

### Important Rules for First-Time View

* ❌ Do NOT show leaderboard
* ❌ Do NOT show rankings
* ❌ Do NOT show advanced stats

Reason:

* Avoid intimidation
* Keep focus on exploration

---

# 3. Competition Page (Kaggle-style)

Once user clicks a competition → switch to full experience.

## Layout

### Header

* Competition title
* Subtitle / description
* "Submit" button (top right)

---

### Tabs Navigation

```text
Overview | Data | Leaderboard | Rules | Submissions
```

Current MVP note:

* `Code`, `Models`, and `Discussion` are deferred in the live web app
* Do not add them back without updating the route contract docs and backend support plan

---

## 3.1 Overview Tab

### Sections

* Competition description
* Task explanation
* Evaluation metric
* Timeline

### Sidebar

* Host
* Participants count
* Submission count
* Tags

---

## 3.2 Data Tab

Show:

* Dataset description
* Download buttons
* File structure preview

Current MVP auth rule:

* Data tab requires sign-in because dataset endpoints require an authenticated session

---

## 3.3 Code Tab (optional v1)

* Starter notebooks
* Example scripts

---

## 3.4 Models Tab (optional v1)

* Pretrained models (if supported)
* Model submissions

---

## 3.5 Discussion Tab

* Forum-style threads

---

## 3.6 Leaderboard Tab

* Table:

  * Rank
  * User/Team
  * Score

Rules:

* Use backend-projected ranking rows
* Support public/private projection toggle

Current MVP note:

* Leaderboard data is available as a dedicated API projection and should not be recomputed in the frontend

---

## 3.7 Rules Tab

Clearly structured:

* Submission limits
* Allowed methods
* Dataset usage rules
* Evaluation method

---

## 3.8 Submissions Tab

User-specific:

Table:

* Submission ID
* Status
* Score
* Time
* Logs link

Current MVP auth rule:

* Submissions tab is user-specific and requires sign-in

---

# 4. Submission Flow UI

## Entry Points

* "Submit" button in header
* "Submit" inside Submissions tab

## Steps

1. Upload file / code
2. Confirm submission
3. Show job status

---

## Job Status UI

Display:

```text
Queued → Running → Scoring → Completed
```

If failed:

* show error message
* show logs

---

# 5. Leaderboard UX Rules

* Default: show only best score per user
* Optional toggle:

  * Public leaderboard
  * Private leaderboard

---

# 6. Navigation Consistency

* Left sidebar (optional for future scale)
* Top navigation for simplicity in MVP

Current implementation rules:

* Keep the header background, border, spacing, and pill sizing identical across pages using the shared site header
* Avoid slight page-to-page navbar height drift
* Prefer shared spacing tokens and shared layout wrappers over route-specific approximations

---

# 7. Admin Panel Guidelines

(No reference UI provided — design from scratch)

## Goals

* Fast internal workflow
* No unnecessary styling complexity
* Focus on control and visibility

---

## Admin Navigation

```text
Dashboard
Competitions
Datasets
Submissions
Workers
Users
Logs
```

---

## 7.1 Admin Dashboard

Show:

* total competitions
* active jobs
* failed jobs
* worker status

---

## 7.2 Competition Management

Create/Edit:

* title
* description
* dataset
* rules
* limits (CPU, RAM, submissions/day)

---

## 7.3 Dataset Management

* upload dataset
* version control
* visibility

---

## 7.4 Submission Monitoring

Table:

* submission id
* user
* status
* worker
* runtime

Actions:

* retry
* cancel

---

## 7.5 Worker Management

Show:

* worker name
* status (online/offline)
* CPU usage
* job count

Actions:

* disable worker
* view logs

---

## 7.6 User Management

* list users
* roles
* ban/suspend

---

## 7.7 Logs & Debugging

* system logs
* job logs
* error tracking

---

# 8. UI Design Principles

## Simplicity First

* Homepage minimal (TLX-style)
* Deep pages rich (Kaggle-style)

## Progressive Disclosure

* Show complexity only after user engages

## Consistency

* Same layout for all competitions
* Same submission flow everywhere

## Feedback

* Always show job state
* Always show errors clearly

---

# 9. MVP UI Scope

## Must-have

* Home page (competition list)
* Competition overview
* Data tab
* Submission system
* Leaderboard

## Can skip initially

* Code tab
* Models tab
* Discussion
* Advanced analytics

---

# Final Summary

* TLX style for entry (simple, clean)
* Kaggle style for engagement (rich, detailed)
* Admin panel optimized for control, not beauty

This hybrid approach keeps onboarding easy while still supporting advanced workflows later.
