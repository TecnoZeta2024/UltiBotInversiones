# Task: Triage and Resolve Test Failures

## Objective
To systematically diagnose, isolate, and resolve test failures using the **SRST (Sistema de Resolución Segmentada de Tests)** protocol. This task is the primary operational directive for the Debugger Agent.

## Workflow (Mandatory)

### Phase 1: Triage & Ticket Creation (Max 5 minutes)

1.  **Initial Diagnosis:**
    - Your first action is to run a diagnostic command to understand the scope of the failures.
    - **Command:** `poetry run pytest --collect-only -q 2>&1 | head -20`
    - Analyze the output to identify the primary error types (e.g., `ImportError`, `TypeError`, `DatabaseError`).

2.  **Categorize & Prioritize:**
    - Based on the diagnosis, classify the errors according to the SRST categories defined in `.clinerules/srst-segmented-resolution-system.md`.
    - Prioritize critical errors that block the execution of other tests (e.g., import errors, fixture setup failures).

3.  **Create SRST Tickets:**
    - Generate a maximum of **three** atomic SRST tickets for the current work session.
    - Use the mandatory ticket template from the SRST rules.
    - Each ticket must define a specific, isolated problem, the files to be touched, and a precise validation command.
    - Document the created tickets in `SRST_TRACKER.md`.

### Phase 2: Micro-Segmented Resolution (Max 15 minutes per ticket)

1.  **Select One Ticket:**
    - Choose the highest-priority ticket from the list you created. Announce which ticket you are working on.

2.  **Load Minimal Context:**
    - Read only the files specified in the ticket. Do not load extraneous files.

3.  **Apply Surgical Fix:**
    - Implement the most direct and precise solution to resolve the specific error described in the ticket.
    - Adhere to all relevant coding standards and best practices defined in the project's `.clinerules`.

4.  **Immediate Validation:**
    - Execute the exact validation command specified in the ticket's `Validación Inmediata` section.
    - **If the fix is successful:** Proceed to the next step.
    - **If the fix fails:** Analyze the new error, revise your approach, and re-attempt the fix. Do not move to another ticket until this one is resolved or deemed a larger issue requiring a new ticket.

5.  **Regression Check:**
    - After a successful validation, run a slightly broader test to ensure your fix has not introduced new problems.
    - **Command:** `poetry run pytest --collect-only -q` or run the tests for the entire module you just modified.

### Phase 3: Documentation & Handoff

1.  **Update Progress:**
    - Document the outcome of the ticket (Resolved, Failed, Needs Escalation) in `SRST_PROGRESS.md`.
    - Update the ticket status in `SRST_TRACKER.md`.

2.  **Monitor Context:**
    - Be constantly aware of your context token usage.
    - If usage exceeds the `ORANGE ALERT` threshold (350k tokens), prepare for a handoff after completing the current ticket.
    - If usage exceeds the `RED ALERT` threshold (400k tokens), you **must** stop, document, and initiate the `new_task` handoff protocol immediately.

3.  **Loop or Conclude:**
    - If there are more tickets in your session's queue and you are within token limits, return to Phase 2, Step 1.
    - If all tickets for the session are complete, provide a summary of the work done and the current state of the test suite.
