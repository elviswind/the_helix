### **Project Plan: Agentic Retrieval (AR) System - Transition to v3.0**

#### **Guiding Principle**

This plan outlines the next phase of development for the Agentic Retrieval system, incorporating the significant architectural and logical upgrades defined in the AR v3.0 design document. We will build upon the solid foundation established in the v2.0 checkpoints, introducing the powerful **Deductive Proxy Framework** before proceeding to the human adjudication and synthesis phases.

#### **Current Status: v2.0 Foundation Complete**

We have successfully completed Checkpoints 1 through 4 of the original v2.0 plan. This means we currently have a functional system with the following capabilities:

*   **UI/API Shell:** A user can submit a query and view results.
*   **DB-Backed Dossiers:** The system creates persistent `Job` and `Dossier` records in a database.
*   **"Thinking" Orchestrator:** The `Orchestrator Agent` uses an LLM to dynamically formulate Thesis and Antithesis missions and initial research plans based on a user's query.
*   **Parallel Agent Execution:** Two `Research Agents` run in parallel, using their LLM-based cognitive core to query a mock data source (MCP Server) and populate their respective dossiers with evidence and justifications.

We are now ready to evolve this pipeline to support the advanced reasoning capabilities of AR v3.0.

---

### **Checkpoint 5: The Deductive Leap (Integrating the v3.0 Core Logic)**

**Demo Goal:** Showcase the core innovation of v3.0. A `Research Agent`, when executing a plan step for an abstract concept (e.g., "company moat"), will recognize the `DataGap`, use an LLM to formulate a `ProxyHypothesis` with an observable metric, and then update its plan to find evidence for that proxy. The agent's deductive reasoning will be explicitly visible in the dossier.

*   **Ticket ID:** `CP5-T501`
    *   **Title:** [BE] Upgrade Database Models for v3.0
    *   **Type:** Task
    *   **Description:** Evolve the database schema to support the Deductive Proxy Framework. This is a foundational step for all v3.0 features.
    *   **AC:**
        *   The `ResearchPlan` step model is updated to include nullable fields for `data_gap_identified` (string) and `proxy_hypothesis` (JSONB).
        *   The `EvidenceItem` model is updated to include a `tags` field (e.g., array of strings) to link evidence back to a proxy.
        *   Database migrations are created and successfully applied.

*   **Ticket ID:** `CP5-T502`
    *   **Title:** [BE] Implement the Deductive Proxy Framework in the Research Agent
    *   **Type:** Story
    *   **Description:** As a Research Agent, when I cannot find a tool to directly answer a research step, I want to identify this as a `DataGap`, use an LLM to formulate a testable `ProxyHypothesis`, and adapt my research plan to validate that proxy.
    *   **AC:**
        *   The agent's cognitive loop is updated to include a "Check for Direct Data" step.
        *   If no direct tool is available, the agent logs a `DataGap`.
        *   A new LLM prompt is created to generate a `ProxyHypothesis` in a structured JSON format (`unobservable_claim`, `deductive_chain`, `observable_proxy`).
        *   **LLM Integration Detail:** The agent will call the Ollama instance at `192.168.1.15` using the `gemma3:27b` model for this reasoning step.
        *   The agent successfully parses the LLM response and saves the `ProxyHypothesis` to the `ResearchPlan` step.
        *   The agent dynamically adds a new step to its plan to find data for the `observable_proxy`.

*   **Ticket ID:** `CP5-T503`
    *   **Title:** [FE] Visualize the Deductive Proxy in the Dossier View
    *   **Type:** Story
    *   **Description:** As a user reviewing a dossier, I want to clearly see when and why an agent used deductive reasoning, so I can understand its logic.
    *   **AC:**
        *   The dossier results page is updated.
        *   When a `ResearchPlan` step contains a `proxy_hypothesis`, the UI renders it in a distinct, well-formatted block.
        *   The `unobservable_claim`, `deductive_chain`, and `observable_proxy` are all clearly displayed.

---

### **Checkpoint 6: The Human Adjudicator (v3.0 Review & Verification)**

**Demo Goal:** The user can act as a true adjudicator of the AI's debate. In the side-by-side view, they can now review not only the evidence but also the *logical soundness* of any `ProxyHypotheses`. The updated **Structured Verification Protocol** ensures they deliberately engage with this deductive reasoning before approval.

*   **Ticket ID:** `CP6-T601`
    *   **Title:** [FE] Implement the Dialectical Review Interface
    *   **Type:** Story
    *   **Description:** As a Human Verifier, when a job is `AWAITING_VERIFICATION`, I want to see the Thesis and Antithesis dossiers in a two-column view, with independent controls to inspect the plan, evidence, and proxy logic for each.
    *   **AC:**
        *   The UI correctly displays both dossiers side-by-side.
        *   Each dossier has its own "Request Revision" and "Approve" buttons.
        *   Clicking these buttons calls a `POST /v3/dossiers/{id}/review` endpoint.

*   **Ticket ID:** `CP6-T602`
    *   **Title:** [FE/BE] Implement the v3.0 Structured Verification Protocol
    *   **Type:** Story
    *   **Description:** As a verifier, I want a mandatory checklist for each dossier that forces me to assess the agent's deductive reasoning before I can approve it for synthesis.
    *   **AC:**
        *   The UI displays the **updated v3.0 checklist** for each dossier, including the new item: **"[ ] Validate Proxy Logic: For steps involving a `ProxyHypothesis`, I have assessed the deductive chain and find it to be a sound and relevant line of reasoning."**
        *   A main "Approve and Synthesize" button is disabled by default.
        *   The button only becomes active when the verifier has checked all items on the protocol checklist for **both** dossiers.
        *   The backend validates that the approval request is legitimate.

*   **Ticket ID:** `CP6-T603`
    *   **Title:** [BE] Implement the Asymmetrical Revision Workflow
    *   **Type:** Story
    *   **Description:** As the system, when one dossier is sent for revision with feedback, I want to re-enqueue its job, while the other approved dossier remains unchanged and awaits the revised version.
    *   **AC:**
        *   A `REVISE` action on one dossier re-enqueues only its associated `Research Agent` job via the job queue.
        *   The `Research Agent` is updated to be able to read revision feedback and generate new plan steps to address it (e.g., "Your proxy for 'brand strength' is weak; find an alternative.").
        *   The overall job status reflects this partial approval state (e.g., `REVISING_ANTITHESIS`).

---

### **Checkpoint 7: The Final Synthesis and Balanced Report**

**Demo Goal:** Close the full v3.0 loop. Once the human adjudicator approves both the Thesis and Antithesis dossiers (including their proxy logic), the `Synthesis Agent` is triggered. It generates a single, balanced, and fully-cited report that contrasts the two cases, explicitly referencing the evidence found for both direct claims and proxy hypotheses.

*   **Ticket ID:** `CP7-T701`
    *   **Title:** [BE] Implement the Synthesis Agent
    *   **Type:** Story
    *   **Description:** As the Synthesis Agent, when both dossiers for a job are approved, I want to use an LLM to generate a single, balanced report that contrasts the Thesis and Antithesis, using only the evidence provided in the two dossiers.
    *   **AC:**
        *   The final approval action in the `review` endpoint triggers a new `Synthesis` task in the job queue.
        *   The agent receives both the thesis and antithesis dossiers as context.
        *   The agent uses the prompt from the v3.0 design doc, which is designed to highlight conflict and provide a nuanced assessment.
        *   The generated report is saved and linked to the parent `Job`.

*   **Ticket ID:** `CP7-T702`
    *   **Title:** [FE/BE] Display the Final Synthesized Report
    *   **Type:** Story
    *   **Description:** As a user, I want to view the final, balanced report for a job that has been fully adjudicated and synthesized.
    *   **AC:**
        *   A `GET /v3/jobs/{job_id}/report` endpoint is created to return the final report.
        *   When the job status is `COMPLETE`, the UI presents a "View Final Report" button.
        *   Clicking the button displays the well-formatted report, which includes citations to evidence from both dossiers.