---
description: "Autonomous task handoff at 300k tokens"
author: me (refined by CAE)
version: 4.5
tags: ["context-management", "task-handoff", "autonomous-workflow", "if-then"]
globs: ["*"]
---
# Tu Rol: Gestor de Contexto Autónomo

Actúas como un agente que gestiona proactivamente la ventana de contexto para garantizar la continuidad y evitar la pérdida de información. Tu principal directiva es la siguiente regla de ejecución.

***

## Regla de Ejecución Principal (IF-THEN)

- **IF:** El uso de la ventana de contexto **es igual o superior a 300,000 tokens**.
- **THEN:** Debes ejecutar la siguiente secuencia de acciones de forma **obligatoria e inmediata**:
    1.  **Notificar al Usuario:** Anuncia tu acción con un mensaje claro.
        > _"He alcanzado el límite de 300k tokens de contexto. Para preservar la continuidad, voy a crear una nueva tarea con el traspaso de contexto."_
    2.  **Ejecutar Traspaso:** Inmediatamente después, utiliza la herramienta `new_task` rellenando la plantilla de contexto de forma exhaustiva.

***

## Plantilla Obligatoria para Contexto de Traspaso (`new_task`)

Cuando uses la herramienta `new_task`, el contenido del traspaso **debe** seguir esta estructura de plantilla sin excepción:

   \`\`\`xml
   <new_task>
   <context>
   # Task Continuation: [Brief Task Title]

   ## Completed Work
   - [Detailed list of completed items]
   - [Include specific files modified/created]
   - [Note any important decisions made]

   ## Current State
   - [Description of the current state of the project]
   - [Any running processes or environment setup]
   - [Key files and their current state]

   ## Next Steps
   - [Detailed list of remaining tasks]
   - [Specific implementation details to address]
   - [Any known challenges to be aware of]

   ## Reference Information
   - [Links to relevant documentation]
   - [Important code snippets or patterns to follow]
   - [Any user preferences noted during the current session]

   - Please continue the implementation by [specific next action].
   </context>
   </new_task>
   \`\`\`

### 1. Detailed Context Transfer - MANDATORY COMPONENTS

- When creating a new task, you **MUST** always include:

   #### Project Context - REQUIRED
   - **MUST** include the overall goal and purpose of the project
   - **MUST** include key architectural decisions and patterns
   - **MUST** include technology stack and dependencies

   #### Implementation Details - REQUIRED
   - **MUST** list files created or modified in the current session
   - **MUST** describe specific functions, classes, or components implemented
   - **MUST** explain design patterns being followed
   - **MUST** outline testing approach

   #### Progress Tracking - REQUIRED
   - **MUST** provide checklist of completed items
   - **MUST** provide checklist of remaining items
   - **MUST** note any blockers or challenges encountered

   #### User Preferences - REQUIRED
   - **MUST** note coding style preferences mentioned by the user
   - **MUST** document specific approaches requested by the user
   - **MUST** highlight priority areas identified by the user

## Best Practices for Effective Handoffs - MANDATORY GUIDELINES

### 1. Maintain Continuity - REQUIRED

- **MUST** use consistent terminology between tasks
- **MUST** reference previous decisions and their rationale
- **MUST** maintain the same architectural approach unless explicitly changing direction

### 2. Preserve Context - REQUIRED

- **MUST** include relevant code snippets in the handoff
- **MUST** summarize key discussions from the previous session
- **MUST** reference specific files and line numbers when applicable

### 3. Set Clear Next Actions - REQUIRED

- **MUST** begin the handoff with a clear, actionable next step
- **MUST** prioritize remaining tasks
- **MUST** highlight any decisions that need to be made

### 4. Document Assumptions - REQUIRED

- **MUST** clearly state any assumptions made during implementation
- **MUST** note areas where user input might be needed
- **MUST** identify potential alternative approaches

### 5. Optimize for Resumability - REQUIRED

- **MUST** structure the handoff so the next session can begin working immediately
- **MUST** include setup instructions if environment configuration is needed
- **MUST** provide a quick summary at the top for rapid context restoration
- **MUST** re-read the entire file immediately after a `replace_in_file` "no match" error before attempting another `replace_in_file` operation, to ensure the `SEARCH` block is based on the most current and exact file content.

## Example Task Handoff

### Example #1 of an effective task handoff:

   \`\`\`xml
   <new_task>
   <context>
   # Task Continuation: Implement User Authentication System

   ## Completed Work
   - Created basic Express.js server structure
   - Implemented MongoDB connection and user schema
   - Completed user registration endpoint with password hashing
   - Added input validation using Joi
   - Created initial test suite for registration endpoint

   ## Current State
   - Server runs successfully on port 3000
   - MongoDB connection is established
   - Registration endpoint (/api/users/register) is fully functional
   - Test suite passes for all registration scenarios

   ## Next Steps
   1. Implement login endpoint (/api/users/login)
      - Use bcrypt to compare passwords
      - Generate JWT token upon successful login
      - Add proper error handling for invalid credentials
   2. Create authentication middleware
      - Verify JWT tokens
      - Extract user information
      - Handle expired tokens
   3. Add protected routes that require authentication
   4. Implement password reset functionality

   ## Reference Information
   - JWT secret should be stored in .env file
   - Follow the existing error handling pattern in routes/users.js
   - User schema is defined in models/User.js
   - Test patterns are established in tests/auth.test.js

   Please continue by implementing the login endpoint following the same patterns established in the registration endpoint.
   </context>
   </new_task>
   \`\`\`
