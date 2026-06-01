# Decisions for Subscription Service API

## 1. What I built and what I skipped
**Built:**
- **State Machine:** Implemented the core logic in `app/state.py`. This ensures the business rules are decoupled from the database and framework, making them easily testable and robust.
- **Unit of Work Pattern:** Managed database transactions in `app/services.py` to ensure that state changes, audit logs, and idempotency checks are committed atomically.
- **Concurrency Control:** Used `with_for_update()` in the repository to prevent race conditions during the "read-modify-write" cycle of billing events.
- **Idempotent Webhook Handler:** A dedicated persistence layer for `event_id` tracking to handle the carrier's "at-least-once" delivery guarantee.
- **Audit Trail:** Automatic generation of audit logs for every meaningful change in subscription state or period.

**Skipped:**
- **Authentication Layer:** Assumed to be handled by an API gateway or middleware, as per the spec.
- **External Notifications:** Logic for sending emails/webhooks back to the user or payment provider was omitted to focus on the core state machine.
- **Complex Billing Cycles:** Stuck to the 7-day trial and 30-day active periods as defined in the configuration.

## 2. Ambiguities I found in the spec
- **Payment failure during trial:** The spec was silent on this. I decided to move the subscription to `grace` rather than immediate cancellation. **Reasoning:** First-time users might have transient payment issues; providing a grace period increases the chances of conversion.
- **User Identification:** The spec mentioned creating a subscription "for a user" but excluded Auth. I decided to omit `user_id` from the `POST` payload. **Reasoning:** In a secure system, `user_id` should come from the verified auth token, not the request body, to prevent "ID spoofing."
- **Overdue Payments:** When a payment succeeds *after* the period end date, I decided to start the new 30-day period from the **payment timestamp**, not the original end date. However, if they pay *early*, the 30 days are appended to the existing end date. This is the fairest model for the user.
- **Terminal State:** I treated `canceled` as a terminal state. Any further payments for a canceled subscription are ignored by the state machine (though they should be flagged for refund in a production environment).

## 3. Data and storage choices
- **Relational Schema (SQLAlchemy):** Used for strict data integrity.
  - `SubscriptionModel`: Stores the current ground truth.
  - `AuditLogModel`: Stores the "why" behind every change, linked by foreign key.
  - `ProcessedEventModel`: A simple, high-speed table for idempotency checks.
- **Storage Choice:** While the app is configured for PostgreSQL-ready logic (row locking), I used an in-memory SQLite database for the test suite to ensure speed and zero-configuration for the reviewer.

## 4. Trade-offs I made
- **Pessimistic vs. Optimistic Locking:** I chose pessimistic locking (`with_for_update`). While optimistic locking (version numbers) is more scalable for high-concurrency read-heavy apps, billing systems require absolute consistency. The risk of "double-spending" or "double-extending" a subscription justifies the slight performance hit of row locks.
- **Models vs Services:** I moved the state transition logic into the domain model (`Subscription`). This keeps the service layer thin and focused only on orchestration (DB commits, repo calls), which is a core principle of Clean Architecture.

## 5. The scenario
**The Case:** Payment succeeds at 14:00:01, User cancels at 14:00:02. Cancel request arrives and is processed *first*.

**Result:** The final state is `CANCELED`.

**Reasoning:**
- My implementation follows a "User Intent First" policy. Once the `user_cancellation` trigger is processed, the state becomes `CANCELED`.
- When the late `payment.succeeded` webhook arrives, the `Subscription.handle_payment_success()` method checks the current state.
- Since the state is already `CANCELED`, the method returns immediately without extending the `period_end_at` or reverting the state.
- **Audit History:**
  1. `trialing` -> `canceled` (Trigger: `user_cancellation`)
  2. The subsequent payment event is recorded in the `processed_events` table (to prevent reprocessing) but produces no further audit logs because it caused no state change.

## 6. Edge cases and failure modes
- **Race Condition on Webhook:** If two identical webhooks arrive at the exact same millisecond, the first one acquires the row lock. The second one will see the `event_id` in the `processed_events` table after the first one commits, and will return early.
- **Payment Success for Overdue Grace:** If a user is in `grace` and pays *after* the grace period ended, but *before* the system processed a failure event to cancel it, they are restored to `active`.
- **Clock Drift:** I used UTC timestamps throughout to avoid issues with server/carrier time differences.

## 7. What I would do differently with more time
- **Background Workers:** Move the `process_webhook` logic to a background task (e.g., Celery) to return a 202 Accepted to the carrier immediately, improving API responsiveness.
- **Soft Deletion:** Implement soft deletes for subscriptions if we ever need to "hide" them from users while keeping the data for analytics.

## 8. How I used AI on this assignment
I used Gemini CLI to manage the project lifecycle:
- **Test Generation:** I provided the domain logic and asked the AI to "try to break it" by generating edge-case tests in `pytest`.
- **Refactoring:** I used the AI to fix some typos I went along with while developing the api.
- **Documentation generation:** While developping I wrote the ambiguities and decisions I made in comments in the code. At the end I asked Gemini to look at the files, delete the comments (to improve code readability), and generate this file. I also used gemini to generate the README file and the mermaid diagrams. 

