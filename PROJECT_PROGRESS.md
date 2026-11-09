# Chap Chap Africa HRMS — Progress Tracker

**Last reviewed:** 9 November 2026  
**Baseline:** HRMS Process and Data-Flow Guide supplied for this project  
**Current checkpoint:** Recruitment and candidate onboarding handoff code has been connected and frontend/backend build checks pass. No live candidate record or outbound email was used for verification.

## Status key

- **In place** — code for the described capability exists.
- **Partial** — some of the process exists, with material workflow or access gaps.
- **Not started** — no corresponding implementation was found.
- **Not verified** — code exists, but a full workflow check has not been completed.

Statuses describe the code review, not production readiness. Existing local modifications are retained; do not treat this tracker as permission to discard them.

## Lifecycle checklist

| Guide stage | Status | Current evidence and remaining work |
|---|---|---|
| 1. Lifecycle and record links | **Partial** | Offer acceptance now creates an `ONBOARDING` employee record, links it to the candidate, and preserves candidate history. Employee activation waits for HR document/detail checks. No unified lifecycle view or live end-to-end handoff verification yet. |
| 2. Recruitment: requisition to offer | **Partial** | HR approval now requires a per-job applicant cap; public listings stop at the cap and applications recheck it at submission. Eligibility rejects retain a reason, interviews save schedule details and email, grades accept outstanding/passed/failed, and failed/declined offers enter the rejection archive (`INTERVIEW_FAILED` / `OFFER_FAILED`). Passed candidates get a result email; offers include HR-authored onboarding instructions and required documents. HR recruitment actions now require HR-role authentication; requisition creation permits a linked HOD and forces their linked department. The HOD ESS route and requisition decision audit remain open. SMTP delivery depends on server configuration. |
| 3. Onboarding | **Partial — main handoff implemented** | Offer acceptance creates an employee in `ONBOARDING` and a required-document checklist. Candidate secure-link form collects personal, contact, family/NOK, statutory and bank details and uploads supported files. HR onboarding queue supports authenticated document download, verified/rejected decisions, and finalization only when required documents and key details are complete. Rejected/missing documents trigger a replacement reminder link. Completion audit/history and a full real-world mail/upload walkthrough remain outstanding. |
| 4. Employee Directory | **Partial** | Employee list and create endpoints exist. Profile update, import/export, and employee document management are not complete. |
| 5. Contracts | **Partial** | Create, list, and activate endpoints exist. Contract documents, fuller employment terms, and verified updates to the employee profile are missing or not established. |
| 6. Attendance and shifts | **Partial** | Authenticated check-in/check-out and attendance listing exist; HOD queries are department-scoped. Shift administration and full payroll handoff are not established. |
| 7. Leave | **Partial / access gap** | Leave request and HOD interface scaffolding exist. Current leave endpoints do not authenticate the caller, `/pending` returns every pending request, and approve/reject does not capture a decision note. The approved-by column exists in the schema migration but is not populated by these handlers. |
| 8. Payroll and payslips | **Partial** | Payroll generation and employee-scoped payslips exist, with role checks on payroll routes. Approval states, reserved deductions, disbursement, and bank-export confirmation from the guide are not implemented. |
| 9. Performance | **Partial — monthly ESS workflow implemented** | Employees and HODs can self-assess by month in ESS. Submission creates an HOD notification; the HOD inbox lists only submitted, unreviewed staff in that department. HOD records punctuality, overtime context, task completion, efficiency, quality, teamwork, a calculated behavior score, final monthly rating, and comments. Completed monthly HOD ratings feed quarter ranking. A synthetic full-cycle walkthrough and best-performer policy approval remain outstanding. |
| 10. Training | **Not started** | No training model, router, or frontend module was found. |
| 11. Employee self-service | **Partial** | The ESS route is registered and available from the main navigation. It has profile, leave, HOD team-approval, requisition, and monthly performance tabs. HOD landing after login and employee-ID-scoped profile data are not complete; leave calls remain unprotected. |
| 12. Analytics | **Partial** | An analytics page and API are present. The API currently contains sample summary figures rather than established cross-module live reporting. |
| 13. Disciplinary cases and grievances | **Partial** | HR can create and list disciplinary cases. Grievance intake, employee responses, case timeline, reporting, and payroll-linked deduction handling are missing. |
| 14. Offboarding | **Partial** | HR can initiate and list an exit request. Clearance is represented by a single status; asset checklist, settlement, archive record, audit history, employee status change, and access closure are missing. |
| 15. Cross-module data handoffs | **Not verified** | Candidate-to-employee linkage is implemented. Employee-linked contracts, attendance, leave, payroll, performance, self-service, and exit handoffs have not been checked across the full lifecycle. |
| 16. Process verification | **Not verified** | No project test suite was found. A read-only check confirmed the active-requisitions API returned HTTP 200 with one approved job, and the public form loaded. No candidate was submitted. The remaining guide verification sequence is outstanding. |

## HOD and requisition target flow

1. A registered HOD signs in and lands in ESS, alongside the employee’s normal self-service.
2. The HOD’s department comes from the linked employee account; the HOD cannot request a role for another department by editing a form field.
3. The HOD submits the role, required education/experience, responsibilities, and selection criteria. Those criteria remain attached to the requisition and drive applicant eligibility checks.
4. The requisition appears in the HR/admin master dashboard as **Pending HR approval**. Only authorized HR/admin users may approve or reject it, with a recorded decision.
5. Approval publishes the opening to the public careers portal. Rejected or pending requisitions remain unpublished.
6. Applicants who meet the saved criteria enter the candidate pipeline; ineligible applications retain their rejection reason and do not enter the active pipeline.
7. The HOD can also view only their department’s leave requests, approve/reject with a note, and submit department-scoped performance ratings/comments from ESS.

**Current state:** items 3–6 have partial scaffolding, including approval applicant limits and the candidate lifecycle through onboarding. Items 1–2 and 7 are not complete; recruitment endpoints still need HR/HOD role enforcement and department scoping before relying on those permissions.

## Cross-cutting blockers

- **Authentication consistency:** login stores the token under `token`; the shared module API clients and layout now accept that key, with `access_token` retained for compatibility. Older Contract and legacy Onboarding screens still read only `access_token`.
- **Server-side authorization:** recruitment HR actions and onboarding review are role protected, and requisition creation is limited to HR or a department-linked HOD. Leave and several ESS endpoints still do not enforce the caller’s role or employee scope. UI-only role checks are not sufficient.
- **HOD landing route:** ESS is registered and visible in navigation. Route HOD logins to ESS after login while retaining the normal employee home view.
- **Decision history:** add approver, decision note, timestamp, and audit entry to HOD leave decisions and HR requisition review.
- **Recruitment/onboarding operational setup:** configure SMTP credentials and a reachable `FRONTEND_URL`; protect recruitment HR actions; verify upload storage/backups and retention rules before handling real candidate documents.

## Recommended implementation order

1. Standardize login token handling and enforce server-side role/employee authorization.
2. Register ESS as a protected route and provide HOD landing with employee self-service still available.
3. Bind requisition creation to the HOD’s department; route it to an HR/admin approval queue; keep approved jobs public and unpublished jobs private.
4. Complete leave approvals with department scoping and decision notes; add the performance rating action to ESS.
5. Walk one clearly synthetic requisition through application cap, eligibility filtering/rejection archive, candidate review, interview, offer response, candidate document submission, HR review, and employee activation. Use a test mailbox and synthetic documents only.
6. Continue the lifecycle modules in guide order and add repeatable workflow checks as each handoff is completed.

## Change log

- **9 Nov 2026:** Created this baseline from the process guide and repository inspection. Confirmed one public approved requisition is visible. No candidate records were created for this review.
- **9 Nov 2026:** Added requisition approval applicant limits, completed interview-result and offer email content, standardized offer-decline archival status/reason, and connected accepted offers to employee-onboarding records. Added the candidate onboarding form, document checklist/upload, HR review/download/finalization flow, required personal/statutory/contact fields, and missing/rejected-document email reminders. Protected recruitment HR actions and bound HOD requisition creation to the linked employee department. Python router/model compilation and the Vite production build succeeded. No database migration was applied manually, no candidate was submitted, and no real email was sent. SMTP setup, full flow walkthrough, HOD ESS integration, and decision audit remain open.

- **9 Nov 2026:** Updated the existing linked account for malatsujacob@gmail.com to `DEVELOPER`, reset its password to the value supplied in the request (stored as a hash), and retained its linked employee profile. Added developer access across HR, HOD, and employee module controls, registered ESS in navigation, and normalized token lookup in the shared API clients. Schema migration applied to the local PostgreSQL database. Verified login and live HTTP 200 access for requisitions, candidate records, onboarding, payroll, performance, attendance, disciplinary, and exit APIs; frontend `/login` returns HTTP 200. Vite production build and Python imports succeeded. No candidate record or email was created/sent.

- **9 Nov 2026:** Added monthly employee self-assessment, department-scoped HOD pending review inbox, HOD notifications with 30-second refresh while ESS is open, behavior dropdowns/checkbox, live behavior score and final monthly rating with comments, and quarter ranking from completed monthly results. HODs are routed back to ESS instead of rating from the standalone Performance page; Performance stays in the sidebar for HR/developer review. Added and applied the monthly performance schema migration. Verified router compilation, Vite production build, live developer login, and HTTP 200 for self history, pending reviews, notifications, quarter ranking, and the `/ess` and `/performance` frontend routes. No performance sample data was inserted.
