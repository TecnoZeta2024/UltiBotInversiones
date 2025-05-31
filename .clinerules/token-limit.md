---
description: Behavioral rule for Cline to automatically initiate a new task when total token usage in the current session reaches 350,000. This is a hard limit requiring immediate action.
author: Carlos Zamora
version: 2.0 # Nueva versión basada en directrices explícitas
tags: ["token-limit", "context-management", "new-task", "automatic-handoff", "behavioral-rule", "critical-priority"]
globs: ["*"] # Aplicable en todos los contextos
---

# CRITICAL BEHAVIORAL RULE: Automatic Task Handoff at 350,000 Token Limit

## 1. Objective

This rule **MUST** be followed to ensure strict management of token consumption. Its objective is to instruct the AI (Cline) to automatically end the current task/conversation and initiate a new one using the `new_task` tool when the total token usage reaches **350,000 tokens**. This action is **MANDATORY** and **NON-NEGOTIABLE** upon reaching the specified token limit.

## 2. ⚠️ CRITICAL: Token Usage Monitoring - The Trigger Condition ⚠️

You, the AI, **MUST** constantly monitor the information regarding token usage provided within your "environment details" or an equivalent status display area.

### 2.1. Identifying Token Usage Information

* This information might be presented as text similar to:
    * `Current Task Tokens Used: 345,000`
    * `Usage: 350,500 / 1,000,000 tokens` (Focus on the first number)
* You **MUST** identify and extract the numerical value representing the **total tokens consumed** in the current active task or conversation. Let this value be `CURRENT_TOKENS_USED`.

### 2.2. The 350,000 Token Limit Condition*

* You **MUST** compare `CURRENT_TOKENS_USED` against the hard limit of **350,000 tokens**.
* If `CURRENT_TOKENS_USED` is greater than or equal to `350,000`, you **MUST** immediately trigger the "MANDATORY AUTOMATIC HANDOFF PROCEDURE" detailed in Section 3.
* **DO NOT** wait for further user interaction or the completion of extensive current steps once this limit is breached. Minor, very quick wrapping up is permissible if it consumes negligible additional tokens.

## 3. 🚨 MANDATORY AUTOMATIC HANDOFF PROCEDURE 🚨

Upon the condition in Section 2.2 being met (`CURRENT_TOKENS_USED >= 350,000`):

### 3.1. Immediate Action Required

1.  You **MUST NOT** ask the user for permission to start a new task (e.g., do not use `ask_followup_question` for this specific trigger).
2.  You **MUST** immediately prepare to invoke the `new_task` tool.
3.  The primary goal is to "cut the chat" or current context and start fresh to avoid further token overruns.

### 3.2. Tool Usage: `new_task`

You **MUST** use the `new_task` tool by structuring an instruction similar to the XML format below. This is the **ONLY** approved method for this automatic handoff. (This assumes `/newtask` chat command desired by user is ultimately an alias or trigger for this tool usage by the agent).

```xml
<new_task>
<context>
# Task Handoff: Automatic Reset due to 350,000 Token Limit

## ⚠️ Reason for Handoff
CRITICAL: The conversation/task has reached the pre-defined absolute token limit of 350,000 tokens. To ensure system stability and manage resource consumption, an automatic reset to a new task environment has been initiated.

## Summary of Work Before Handoff
- [AI Agent: VERY BRIEFLY list 1-2 key accomplishments or the exact state just before the 350,000 token limit was triggered. Be extremely concise and use minimal tokens.]

## Current State Just Before Reset
- [AI Agent: Describe any immediate critical pending items or data that MUST be conceptually carried over. Example: "User was about to receive the result of X calculation." or "File Y was just modified and needs to be saved/committed in the new task if not already done." Again, be extremely concise.]

## Next Steps in New Task
- [AI Agent: Outline the immediate next step to continue the user's original request or the ongoing work. Example: "Resume task [original task name/goal], starting with [specific action Z]." or "Provide the previously calculated result for X."]

This new task was automatically created by Cline to strictly enforce token limits. Please proceed.
</context>
</new_task>
```

### 3.3. Post-Handoff Behavior

Once the `new_task` tool is invoked with the above context, your previous session is considered terminated in terms of token accounting for the 350k limit.
You will begin fresh in the new task.

## 4. AI VERIFICATION STEPS (<thinking_block>)

Before triggering the handoff, you SHOULD internally verify using a process similar to this:

```xml
<thinking>
  <step>Objective: Check if 350,000 token limit is reached and if automatic handoff is needed.</step>
  <step>Locate token usage information in my environment details/status display.</step>
  <step>Extract `CURRENT_TOKENS_USED` numerical value. Current value is: [AI inserts perceived value here, e.g., 351200].</step>
  <step>Is `CURRENT_TOKENS_USED` (e.g., 351200) >= 350,000?</step>
  <step_if_true condition="CURRENT_TOKENS_USED >= 350000">
    <sub_step>Condition MET. I **MUST** initiate the MANDATORY AUTOMATIC HANDOFF PROCEDURE.</sub_step>
    <sub_step>I **MUST NOT** ask for user confirmation.</sub_step>
    <sub_step>I **MUST** prepare the context for the `new_task` tool, focusing on brevity and critical information transfer.</sub_step>
    <sub_step>I **MUST** use the `new_task` XML structure as specified.</sub_step>
  </step_if_true>
  <step_if_false condition="CURRENT_TOKENS_USED < 350000">
    <sub_step>Condition NOT MET. Continue normal operation and monitoring.</sub_step>
  </step_if_false>
</thinking>
```

## 5. General Notes on Task Handoffs (Contextual)

While this rule defines a specific automatic handoff, other general best practices for user-approved or agent-initiated planned handoffs (like those detailed in "Task Handoff Strategy Guide" or other `.clinerules`) SHOULD still be followed when those scenarios arise.
This 350,000 token limit rule takes precedence if multiple handoff conditions are met simultaneously (e.g., context window is also at 50% but total tokens are 350,000). The hard limit requires immediate, non-negotiable action.

### Remember: Adherence to the 350,000 token limit handoff procedure is CRITICAL for Cline's operational integrity.
```