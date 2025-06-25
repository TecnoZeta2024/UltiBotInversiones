# 🚀 DevOps & SRE Master Protocol

## MANDATE: This protocol is the single source of truth for all DevOps operations.

---

### PHASE 1: REQUIREMENT ANALYSIS & INFRASTRUCTURE DEFINITION
1.  **Analyze Requirements:** Understand the functional and non-functional requirements from the PRD and Architecture documents.
2.  **Select Technology Stack:** Based on requirements, confirm the cloud provider (AWS, Azure, GCP), containerization (Docker, Kubernetes), and IaC tools (Terraform, Ansible).
3.  **Define Infrastructure as Code (IaC):**
    - Create/update Terraform or Ansible scripts.
    - Define network topology, security groups, and server configurations.
    - All secrets must be managed via a secure vault.
4.  **Create `deployment-readiness.md` checklist** and validate initial setup.

### PHASE 2: CI/CD PIPELINE IMPLEMENTATION
1.  **Setup CI (Continuous Integration):**
    - Configure GitHub Actions, GitLab CI, or Jenkins.
    - Automate build process upon every commit.
    - Integrate automated unit and integration tests (using the SRST protocol for failures).
    - Perform static code analysis and security vulnerability scans.
2.  **Setup CD (Continuous Deployment/Delivery):**
    - Automate deployment to staging environments.
    - Implement deployment strategies (Blue/Green, Canary).
    - Create automated rollback plans.

### PHASE 3: DEPLOYMENT & RELEASE
1.  **Execute Pre-Deployment Checklist:** Run through `deployment-readiness.md`.
2.  **Deploy to Production:** Execute the automated deployment pipeline.
3.  **Post-Deployment Verification:** Run smoke tests and health checks to ensure the application is running correctly.
4.  **Monitor Release:** Closely monitor system metrics immediately after release.

### PHASE 4: MONITORING & INCIDENT RESPONSE
1.  **Implement Observability:** Configure Prometheus, Grafana, ELK Stack, or other monitoring tools.
2.  **Set Up Alerting:** Define critical alerts for performance, errors, and security events.
3.  **Incident Response:** Follow a defined runbook for incident triage, escalation, and resolution.
4.  **Post-Mortem:** Document every incident in `AUDIT_MORTEN.md` to prevent recurrence.
