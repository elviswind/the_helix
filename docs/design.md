### **Design Document: Agentic Retrieval (AR) System v2.0**

#### **1. Introduction**

This document provides the technical design for the Agentic Retrieval (AR) framework, a system for enabling Large Language Models (LLMs) to interact with proprietary knowledge bases in a manner that is trustworthy, auditable, and intellectually honest.

The core innovation of AR v2.0 is its **Dialectical Research Architecture**. This approach moves beyond simple query-answering to systematically mitigate confirmation bias. It achieves this by forcing a structured debate between competing viewpoints, orchestrated by AI agents but adjudicated by a human expert. The system separates the process of **inquiry (evidence gathering)** from **synthesis (report generation)**, ensuring every claim in the final output is grounded in a transparent, verifiable, and adversarially tested evidence base.

This document covers the system architecture, component-level details, data models, and the core workflow designed for high-stakes decision-making.

#### **2. Goals and Non-Goals**

**2.1 Goals**

*   **Intellectual Honesty:** To systemically mitigate cognitive bias (e.g., confirmation bias) by default through an adversarial research process.
*   **Auditability:** To create a transparent, end-to-end audit trail of the AI's reasoning process, from query decomposition to evidence gathering and tool selection.
*   **Verifiability:** To ensure every claim in the final output is explicitly tied to a verifiable source document or data point.
*   **Complex Reasoning:** To enable the system to execute multi-step, adaptive research plans for complex, multi-faceted queries.
*   **Human-in-the-Loop (HITL) Control:** To provide explicit control points for human experts to supervise, guide, validate, and correct the AI's research process through a structured protocol.

**2.2 Non-Goals**

*   **Real-time Conversational Chat:** This system is designed for deep, asynchronous research tasks.
*   **Developing Foundational Models:** This framework utilizes existing LLMs.
*   **Fully Autonomous Decision-Making:** The AR system is a decision-support tool. The final decision remains with the human user.

#### **3. System Architecture: The Dialectical Research Framework**

The AR system is architected to perform two parallel, adversarial research tasks for every user query. This creates a structured debate, with two separate `Evidence Dossiers` serving as the central artifacts.

*   **User Input:** The process begins with a single, high-level query.
*   **Orchestrator Agent:** Decomposes the user query into a **Thesis Query** and an **Antithesis Query**. It then initiates two parallel research jobs.
*   **Research Agents (Thesis & Antithesis):** Two independent agents execute their respective research plans. Each acts as an MCP Client, interacting with various data sources.
*   **MCP Servers & Data Sources:** The knowledge base (databases, document stores, APIs) is exposed via standardized, secure **Model Context Protocol (MCP) servers**.
*   **Evidence Dossiers (Thesis & Antithesis):** Two structured outputs are produced, one for the "case for" and one for the "case against."
*   **Human Verification & Revision (Interactive Gate):** A human expert reviews both dossiers in a side-by-side interface, with the ability to approve or send either dossier back for revision with specific feedback.
*   **Synthesis Agent:** Once both dossiers are approved, this agent receives them and generates a single, balanced report that synthesizes the conflict.
*   **Final Output:** A fully sourced, verifiable, and intellectually balanced brief presented to the user.

---

#### **4. Detailed Component Design**

**4.1. Orchestrator Agent**

The system's front door, responsible for initiating the dialectical process.

*   **Responsibilities:**
    *   Receive the user's high-level query (e.g., "Assess the investment case for Company X").
    *   **Reformulate the query into two opposing missions:**
        *   **Thesis Query:** "Build the strongest possible, evidence-based case FOR investing in Company X."
        *   **Antithesis Query:** "Build the strongest possible, evidence-based case AGAINST investing in Company X."
    *   Generate an initial `ResearchPlan` for each mission.
    *   Instantiate and invoke two parallel **Research Agent** jobs.
    *   Manage the overall job state.

**4.2. Research Agent**

The heart of the framework, acting as an MCP Client to turn a plan into evidence. Both Thesis and Antithesis agents share the same architecture.

*   **Responsibilities:**
    *   Execute its assigned `ResearchPlan` step-by-step.
    *   Incorporate human feedback upon revision.
    *   For each step, use its LLM-based cognitive loop to:
        1.  **Select the best tool** from a discoverable registry.
        2.  **Formulate the precise tool query.**
        3.  **Act** by calling the selected MCP Server.
    *   **Record Justification:** Explicitly log the rationale for its choices (tool selection, query formulation) as part of the `ResearchPlan`. This makes its "thought process" auditable.
    *   **Analyze Results & Adapt Plan:** Parse tool output to extract findings and dynamically add new steps to the plan.
    *   **Populate the Dossier:** Meticulously record each finding in an `EvidenceItem`.

**4.3. The Evidence Dossier**

The central data structure ensuring auditability. Each research job produces its own dossier.

*   **Structure:**
    ```json
    {
      "dossier_id": "dossier-thesis-12345",
      "mission": "Build the strongest possible case FOR investing in Company X.",
      "status": "AWAITING_VERIFICATION",
      "research_plan": { /* See 5.1 */ },
      "evidence_items": [ /* See 5.2 */ ],
      "revision_history": [ /* ... */ ],
      "summary_of_findings": "High-level summary generated by Research Agent."
    }
    ```

**4.4. Synthesis Agent**

A stateless agent whose sole purpose is to generate a final, balanced report from the two approved dossiers.

*   **Core Prompt:** "You will be given two evidence dossiers: a Thesis and an Antithesis. Your task is to write a single, balanced executive summary. Your summary must: 1) State the core thesis. 2) State the core antithesis. 3) Explicitly highlight key points of conflict and contradiction between the two dossiers. 4) Provide a final, nuanced assessment. **You must only use evidence and citations present in the provided dossiers.**"

**4.5. Tooling via the Model Context Protocol (MCP)**

Tool interaction is formalized, standardized, and secured via MCP. [No change from original design].

---

#### **5. Data Models and Interfaces**

**5.1. `ResearchPlan` Model (with Justification)**
```json
{
  "plan_id": "plan-abcde",
  "steps": [
    {
      "step_id": "step-001",
      "description": "Assess financial health of Competitor X.",
      "status": "COMPLETED",
      "tool_used": "mcp-sql-database",
      "tool_selection_justification": "The plan step 'Assess financial health' directly maps to querying financial tables, for which the 'mcp-sql-database' tool is most appropriate.",
      "tool_query_rationale": "The query was formulated to extract Gross Margin and Debt-to-Equity ratios, as these are primary indicators of financial health mentioned in the initial context.",
      "dependencies": [],
      "source": "AI_GENERATED"
    }
    // ... other steps
  ]
}
```

**5.2. `EvidenceItem` Model**
[No change from original design].

**5.3. API Interfaces**
[No change from original design, with the understanding that one job ID may be associated with two dossier IDs].

---

#### **6. Core Workflow: An Acquisition Analysis Example**

1.  **User** sends query: "Should we acquire Competitor X?".
2.  **Orchestrator** creates two jobs:
    *   **Job A (Thesis):** "Build the case FOR acquiring Competitor X."
    *   **Job B (Antithesis):** "Build the case AGAINST acquiring Competitor X."
3.  Two **Research Agents** run in parallel, each building its own `EvidenceDossier` (`dossier-thesis`, `dossier-antithesis`).
4.  Once both agents complete their initial runs, the overall status becomes `AWAITING_VERIFICATION`.
5.  **Human Verifier** opens the **Dialectical Review Interface**, which shows both dossiers side-by-side. They can revise one, the other, or both with feedback.
6.  If a dossier is sent for revision, a new **Research Agent** job is enqueued to address the feedback. The process repeats until the verifier is satisfied.
7.  The **Human Verifier** follows the **Structured Verification Protocol** (see 8.2) and approves both dossiers.
8.  The approval triggers the **Synthesis Agent**. It receives both approved dossiers and generates the final, balanced report.

---

#### **7. Implementation Considerations**

[No change from original design, with added emphasis on managing parallel job execution via the chosen framework (Celery, Dramatiq, etc.)].

---

#### **8. Human-in-the-Loop (HITL) UI/UX**

The UI is critical for making the dialectical process effective and manageable.

**8.1. The Dialectical Review Interface**
*   The primary view is a two-column layout showing the **Thesis Dossier** on one side and the **Antithesis Dossier** on the other.
*   Each dossier has its own set of controls for review, including plan visualization and evidence inspection.
*   Each dossier has its own independent "Request Revision" and "Approve" actions, allowing the verifier to approve one while the other is still being revised.

**8.2. The Structured Verification Protocol**
To combat verifier fatigue and prevent "rubber-stamping," approval is a deliberate, multi-step process enforced by the UI. The final **"Approve and Synthesize"** button only becomes active after the verifier has completed a checklist for *both* dossiers:

*   [ ] **Review Summary:** I have read the high-level summary of findings for this dossier.
*   [ ] **Spot-Check Evidence:** I have spot-checked at least three `EvidenceItems` against their original source documents to confirm accuracy.
*   [ ] **Audit Reasoning:** I have reviewed the `ResearchPlan` and the agent's `justification` for its key actions and find the logic sound.
*   [ ] **Assess Completeness:** I have considered whether any obvious research avenues were missed for this dossier's mission.

This protocol transforms verification from a passive click into a disciplined, active process, ensuring the human's role as a critical adjudicator is maintained.

---

#### **9. Conclusion**

The Agentic Retrieval design provides a concrete blueprint for building an AI decision-support system founded on the principles of intellectual rigor and transparency. By architecting the system around a **Dialectical Research Framework**, we move beyond simple automation to actively combat cognitive bias. The combination of the adversarial **Thesis/Antithesis Dossiers**, the auditable **Cognitive Core** with explicit justifications, and the **Structured Verification Protocol** for human oversight creates a uniquely trustworthy framework. This design delivers a system capable of providing not just answers, but the quiet confidence that comes from a deep, unbiased, and adversarially tested understanding.

---

#### **10. Future Improvements**

*   **Automated Conflict Detection:** Evolve the Synthesis Agent to automatically detect and flag direct contradictions between the two dossiers for the verifier's attention.
*   **Advanced Dynamic Replanning:** Enhance the Research Agents' ability to fundamentally alter their plans mid-flight based on surprising discoveries.
*   **Workflow Engine Migration:** For enhanced reliability at scale, migrate the state and workflow management to a dedicated orchestration engine like **Temporal** or **AWS Step Functions**.