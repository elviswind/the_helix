### **Project Plan: Agentic Retrieval (AR) System v2.0 - Agile Checkpoints**

#### **Guiding Principle**

Our development will follow an iterative, checkpoint-based model. Each checkpoint delivers a demonstrable vertical slice of functionality, allowing for early and continuous user feedback. We will introduce the core "Dialectical" (Thesis vs. Antithesis) concept early in the process, even with mock data, to ensure the UI and backend architecture are built on the correct foundation from the start.

---

### **Checkpoint 1: The Interactive Mockup (The Shell)**

**Demo Goal:** A user can visit a webpage, enter a research query, and see a hardcoded, fake result representing the future dialectical view. This validates the core UI flow and provides a tangible artifact for stakeholder feedback on the two-sided layout.

*   **Ticket ID:** `CP1-T101`
    *   **Title:** [FE] Create Research Initiation Page
    *   **Type:** Story
    *   **Description:** As a user, I want a simple webpage with a text input field and a "Start Research" button so I can submit my query.
    *   **AC:**
        *   A basic UI is deployed and accessible via a URL.
        *   The page contains a large text area for the query and a button.
        *   Clicking the button triggers a call to a mock backend API.

*   **Ticket ID:** `CP1-T102`
    *   **Title:** [BE] Create Mock Dialectical Research Endpoint
    *   **Type:** Task
    *   **Description:** Create a single API endpoint that accepts a query, simulates a delay, and returns a hardcoded job ID.
    *   **AC:**
        *   A `POST /v2/research` endpoint exists.
        *   It accepts a `{ "query": "..." }` payload.
        *   It returns a `202 Accepted` with a `{ "job_id": "mock-job-v2-123" }`.

*   **Ticket ID:** `CP1-T103`
    *   **Title:** [FE/BE] Create Mock Dialectical Result Page
    *   **Type:** Story
    *   **Description:** As a user, after submitting my query, I want to be taken to a page that shows the job is in progress and then displays the final (mocked) **Thesis and Antithesis** results side-by-side.
    *   **AC:**
        *   The UI redirects to `/research/mock-job-v2-123`.
        *   This page polls a `GET /v2/research/{job_id}/status` endpoint.
        *   The mock status endpoint returns `{ "status": "RESEARCHING" }` and after a delay, returns `{ "status": "AWAITING_VERIFICATION", "thesis_dossier_id": "mock-thesis", "antithesis_dossier_id": "mock-antithesis" }`.
        *   A new `GET /v2/dossiers/{dossier_id}` endpoint returns a hardcoded JSON dossier.
        *   The UI fetches both mock dossiers and renders them in a **two-column layout**.

---

### **Checkpoint 2: The "Canned" Dialectical Dossiers**

**Demo Goal:** The system now uses a real database. A user's query creates a single `Job` record linked to two persistent `Dossier` records (Thesis & Antithesis), which are populated with pre-defined, "canned" evidence. This makes the dialectical structure real in the data layer.

*   **Ticket ID:** `CP2-T201`
    *   **Title:** [BE] Implement Core v2.0 Database Models
    *   **Type:** Task
    *   **Description:** Implement the `Job`, `EvidenceDossier`, `ResearchPlan`, and `EvidenceItem` database schemas, ensuring a `Job` can be linked to two `Dossiers`.
    *   **AC:**
        *   Database tables are created via migrations.
        *   A `Job` model has one-to-many relationship with `EvidenceDossier`.
        *   Application code includes classes for manipulating these data models.

*   **Ticket ID:** `CP2-T202`
    *   **Title:** [BE] Replace Mock Endpoints with DB-Backed Endpoints
    *   **Type:** Story
    *   **Description:** As the system, when a user starts a query, I want to create a real `Job` record and two associated `Dossier` records in the database, then run a "canned" process to populate both with predefined evidence.
    *   **AC:**
        *   The `POST /v2/research` endpoint creates one `Job` and two `Dossier` records (one `thesis`, one `antithesis`) with `status: PENDING`.
        *   A simple, non-AI script runs, populating each Dossier with a fixed set of `EvidenceItems`.
        *   The script updates both Dossiers' status to `AWAITING_VERIFICATION`.

*   **Ticket ID:** `CP2-T203`
    *   **Title:** [FE] Display Real Dossier Data from Two Sources
    *   **Type:** Story
    *   **Description:** As a user, I want the results page to display the actual data from the two dossiers created for my job.
    *   **AC:**
        *   The results page correctly fetches the `Job` status, gets both `dossier_ids`, and calls `GET /v2/dossiers/{id}` for each one.
        *   The two-column UI correctly renders the plan and evidence items for the Thesis and Antithesis dossiers from the database.

---

### **Checkpoint 3: The "Thinking" Orchestrator Agent**

**IMPORTANT** LLM used in this project is accessed via ollama, which is hosted on ip 192.168.1.15, the model name is "gemma3:27b". 

**Demo Goal:** Introduce the first LLM. The `Orchestrator Agent` now dynamically generates the **Thesis and Antithesis missions** and their respective `ResearchPlans` based on the user's actual query. The system is no longer canned; it is reasoning about opposition.

*   **Ticket ID:** `CP3-T301`
    *   **Title:** [BE] Integrate Job Queue System
    *   **Type:** Task
    *   **Description:** Integrate Celery/Dramatiq to manage the overall research job asynchronously.
    *   **AC:**
        *   The `POST /v2/research` endpoint now enqueues an `Orchestrator` job.
        *   A worker process can pick up and execute the job.

*   **Ticket ID:** `CP3-T302`
    *   **Title:** [BE] Implement Orchestrator Agent's Dialectical Formulation
    *   **Type:** Story
    *   **Description:** As the Orchestrator Agent, when a new job starts, I want to use an LLM to reformulate the user's query into a **Thesis Mission** and an **Antithesis Mission**, and generate a starting `ResearchPlan` for each.
    *   **AC:**
        *   The agent calls an LLM API with a prompt to generate two opposing research missions.
        *   The agent parses the LLM response.
        *   The agent saves the structured `ResearchPlan` for the Thesis to the first dossier and the `ResearchPlan` for the Antithesis to the second dossier.
        *   For this checkpoint, the agent will mark all plan steps as `COMPLETED` without actually executing them.

---

### **Checkpoint 4: Parallel Agents Connecting to Data**

**Demo Goal:** The two `Research Agents` now execute their plans in parallel, calling a real data source via MCP and populating their respective dossiers with dynamically retrieved evidence and justifications. The core agentic loop is now complete for both sides of the argument.

*   **Ticket ID:** `CP4-T401`
    *   **Title:** [BE] Implement a Mock MCP Server
    *   **Type:** Task
    *   **Description:** Create and deploy a mock MCP server that adheres to the MCP spec and returns predictable data for testing.
    *   **AC:**
        *   The server implements `/manifest` and `/search` endpoints. It can be run as a standalone service.

*   **Ticket ID:** `CP4-T402`
    *   **Title:** [BE] Implement Research Agent's Cognitive Core Loop
    *   **Type:** Story
    *   **Description:** As a Research Agent, for each plan step, I want to use an LLM to: select a tool, formulate a query, call the tool, and record the `tool_selection_justification` and `tool_query_rationale` for my choices.
    *   **AC:**
        *   The agent's "Tool Selection" and "Query Formulation" prompts work correctly.
        *   The agent successfully calls the mock MCP server.
        *   The agent correctly records its reasoning in the `ResearchPlan` step model.

*   **Ticket ID:** `CP4-T403`
    *   **Title:** [BE] Enable Parallel Research Job Execution
    *   **Type:** Task
    *   **Description:** As the Orchestrator, after creating the two plans, I want to enqueue two separate `Research Agent` jobs to run in parallel, one for each dossier.
    *   **AC:**
        *   The `Orchestrator` task dispatches two new tasks to the job queue.
        *   The system can execute multiple `Research Agent` tasks concurrently.
        *   Each agent correctly populates its assigned dossier with `EvidenceItems` based on tool results.

---

### **Checkpoint 5: The Dialectical Review Interface & Structured Verification**

**Demo Goal:** The user can now act as a true verifier within the dialectical framework. They can review both completed dossiers in the side-by-side UI and must complete the **Structured Verification Protocol** checklist for both before approval is possible.

*   **Ticket ID:** `CP5-T501`
    *   **Title:** [FE] Implement the Dialectical Review Interface
    *   **Type:** Story
    *   **Description:** As a Human Verifier, when a job is `AWAITING_VERIFICATION`, I want to see the Thesis and Antithesis dossiers in a two-column view, with independent controls to inspect the plan and evidence for each.
    *   **AC:**
        *   The UI correctly displays both dossiers.
        *   Each dossier has its own "Request Revision" and "Approve" buttons.
        *   Clicking these buttons calls a `POST /v2/dossiers/{id}/review` endpoint.

*   **Ticket ID:** `CP5-T502`
    *   **Title:** [FE/BE] Implement the Structured Verification Protocol
    *   **Type:** Story
    *   **Description:** As a verifier, I want a checklist for each dossier that I must complete before I can give my final approval for synthesis, to ensure I review the work thoroughly.
    *   **AC:**
        *   The UI displays the checklist from the design document for each dossier.
        *   A main "Approve and Synthesize" button is disabled by default.
        *   The button only becomes active when the verifier has checked all items on the protocol checklist for **both** dossiers.

*   **Ticket ID:** `CP5-T503`
    *   **Title:** [BE] Implement the Asymmetrical Revision Workflow
    *   **Type:** Story
    *   **Description:** As the system, when one dossier is sent for revision, I want to re-enqueue its job with feedback, while the other approved dossier remains unchanged.
    *   **AC:**
        *   A `REVISE` action on one dossier re-enqueues only its associated research job.
        *   The Research Agent is updated to read the revision feedback and generate new plan steps to address it.
        *   The overall job status reflects this partial approval state (e.g., `REVISING_THESIS`).

---

### **Checkpoint 6: The Synthesis and Final Balanced Report**

**Demo Goal:** Close the loop. Once both dossiers are approved by the verifier, the `Synthesis Agent` is triggered to generate a single, balanced, and fully-cited report that explicitly addresses the conflict between the two cases. The full end-to-end v2.0 journey is now complete.

*   **Ticket ID:** `CP6-T601`
    *   **Title:** [BE] Implement the Synthesis Agent
    *   **Type:** Story
    *   **Description:** As the Synthesis Agent, when both dossiers for a job are approved, I want to use an LLM to generate a single, balanced report that contrasts the Thesis and Antithesis, using only the evidence provided in the two dossiers.
    *   **AC:**
        *   A new task is triggered by the final approval action.
        *   The agent receives both the thesis and antithesis dossiers as context.
        *   The agent uses a prompt specifically designed to highlight points of conflict and provide a nuanced assessment.
        *   The generated report includes citations to `EvidenceItems` from both dossiers.

*   **Ticket ID:** `CP6-T602`
    *   **Title:** [FE/BE] Display the Final Synthesized Report
    *   **Type:** Story
    *   **Description:** As a user, I want to view the final, balanced report for a job I have fully approved.
    *   **AC:**
        *   A `GET /v2/jobs/{job_id}/report` endpoint returns the generated report.
        *   The UI shows a "View Final Report" button once the job status is `COMPLETE`.
        *   Clicking the button displays the well-formatted Markdown report.