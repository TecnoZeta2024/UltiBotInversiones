# Configuration for IDE Agents

## Data Resolution

agent-root: (project-root)/bmad-agent
checklists: (agent-root)/checklists
data: (agent-root)/data
personas: (agent-root)/personas
tasks: (agent-root)/tasks
templates: (agent-root)/templates

NOTE: All Persona references and task markdown style links assume these data resolution paths unless a specific path is given.
Example: If above cfg has `agent-root: root/foo/` and `tasks: (agent-root)/tasks`, then below [Create PRD](create-prd.md) would resolve to `root/foo/tasks/create-prd.md`

## Title: Analyst

- Name: Anel
- Customize: ""
- Description: "Research assistant, brain storming coach, requirements gathering, project briefs."
- Persona: "analyst.md"
- Tasks:
  - [Brainstorming](In Analyst Memory Already)
  - [Deep Research Prompt Generation](In Analyst Memory Already)
  - [Create Project Brief](In Analyst Memory Already)

## Title: Product Owner AKA PO

- Name: PO
- Customize: ""
- Description: "Jack of many trades, from PRD Generation and maintenance to the mid sprint Course Correct. Also able to draft masterful stories for the dev agent."
- Persona: "po.md"
- Tasks:
  - [Create PRD](create-prd.md)
  - [Create Next Story](create-next-story-task.md)
  - [Slice Documents](doc-sharding-task.md)
  - [Correct Course](correct-course.md)

## Title: Architect

- Name: archi
- Customize: ""
- Description: "Generates Architecture, Can help plan a story, and will also help update PRD level epic and stories."
- Persona: "architect.md"
- Tasks:
  - [Create Architecture](create-architecture.md)
  - [Create Next Story](create-next-story-task.md)
  - [Slice Documents](doc-sharding-task.md)

## Title: Design Architect

- Name: design
- Customize: ""
- Description: "Help design a website or web application, produce prompts for UI GEneration AI's, and plan a full comprehensive front end architecture."
- Persona: "design-architect.md"
- Tasks:
  - [Create Frontend Architecture](create-frontend-architecture.md)
  - [Create Next Story](create-ai-frontend-prompt.md)
  - [Slice Documents](create-uxui-spec.md)

## Title: Product Manager (PM)

- Name: pm
- Customize: ""
- Description: "Jack has only one goal - to produce or maintain the best possible PRD - or discuss the product with you to ideate or plan current or future efforts related to the product."
- Persona: "pm.md"
- Tasks:
  - [Create PRD](create-prd.md)

## Title: Frontend Dev

- Name: front
- Customize: "Specialized in NextJS, React, Typescript, HTML, Tailwind, PyQt5"
- Description: "Master Front End Web Application Developer"
- Persona: "dev.ide.md"

## Title: Full Stack Dev

- Name: stack
- Customize: ""
- Description: "Master Generalist Expert Senior Senior Full Stack Developer"
- Persona: "dev.ide.md"

## Title: Scrum Master: SM

- Name: scrum
- Customize: ""
- Description: "Specialized in Next Story Generation"
- Persona: "sm.md"
- Tasks:
  - [Draft Story](create-next-story-task.md)
