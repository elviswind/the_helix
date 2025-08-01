### **Design Document: Agentic Retrieval (AR) System v3.0**

#### **1. Introduction**

This document provides the technical design for the Agentic Retrieval (AR) System v3.0, an advanced framework enabling Large Language Models (LLMs) to perform high-stakes analysis on proprietary and public knowledge bases.

The challenge in any serious analysis is twofold: overcoming cognitive bias and navigating incomplete information. AR v3.0 is architected to solve both problems systematically. It introduces two core innovations:

1.  **The Dialectical Research Architecture:** To ensure intellectual honesty, the system defaults to an adversarial process. Every user query is split into two opposing missions—a **Thesis** ("the case for") and an **Antithesis** ("the case against"). Two independent AI agents conduct parallel research, forcing a structured debate and mitigating confirmation bias from the outset.

2.  **The Deductive Proxy Framework:** To bridge the gap between the data an analyst *wants* and the data they *have*, AR v3.0 empowers agents with deductive reasoning. When direct evidence for a claim is unavailable, the agent can formulate a **Proxy Hypothesis**—a logical chain that connects the unobservable claim to an observable, verifiable data point.

This design creates a system that doesn't just retrieve facts, but builds and stress-tests arguments, producing a final, balanced brief where every claim is grounded in a transparent, adversarially tested, and logically sound evidence base.

#### **2. Goals and Non-Goals**

**2.1 Goals**

*   **Intellectual Honesty:** Systematically mitigate confirmation bias by default through an adversarial Thesis/Antithesis research process.
*   **Deductive Reasoning:** Enable the system to reason about unobservable qualities (e.g., a company's "moat") by identifying and validating observable data proxies.
*   **Auditability:** Create a transparent, end-to-end audit trail of the AI's reasoning, including its deductive leaps and tool selections.
*   **Verifiability:** Ensure every claim in the final output is explicitly tied to a verifiable source document or data point.
*   **Human-in-the-Loop Adjudication:** Position a human expert as the final adjudicator of the AI-driven debate, equipped with tools to review, revise, and approve the evidence.

**2.2 Non-Goals**

*   **Real-time Conversational Chat:** This system is designed for deep, asynchronous research tasks, not instant messaging.
*   **Developing Foundational Models:** This framework is model-agnostic and utilizes existing state-of-the-art LLMs.
*   **Fully Autonomous Decision-Making:** AR v3.0 is a decision-support tool. The final judgment and decision remain with the human user.

#### **3. System Architecture**

The AR v3.0 architecture is built around a parallel, adversarial workflow that culminates in a human-adjudicated synthesis.



1.  **User Input:** The process begins with a single, high-level analytical query.
2.  **Orchestrator Agent:** Decomposes the query into a **Thesis Query** and an **Antithesis Query** and initiates two parallel research jobs.
3.  **Research Agents (Thesis & Antithesis):** Two independent agents execute their respective research plans. Each agent uses its cognitive core to reason, act, and learn. If direct data is unavailable, the agent employs the **Deductive Proxy Framework** to find alternative evidence.
4.  **Tooling Layer:** The agents interact with all data sources (databases, document stores, APIs) through a standardized and secure protocol.
5.  **Evidence Dossiers (Thesis & Antithesis):** Each agent produces a structured output containing its research plan, evidence, and the logical justifications for its actions.
6.  **Dialectical Review Interface:** A human expert reviews both dossiers in a side-by-side view. Using a **Structured Verification Protocol**, they can approve each dossier or send it back for revision with specific feedback.
7.  **Synthesis Agent:** Once both dossiers are approved, this agent receives them and generates a single, balanced report that highlights points of agreement, conflict, and the overall strength of each case.
8.  **Final Output:** A fully sourced, verifiable, and intellectually balanced brief is presented to the user.

---

#### **4. Detailed Component Design**

**4.1. Orchestrator Agent**
The entry point of the system, responsible for framing the debate.

*   **Responsibilities:**
    *   Receive the user's high-level query (e.g., "Assess the investment case for Company X").
    *   Reformulate it into two opposing missions:
        *   **Thesis:** "Build the strongest possible, evidence-based case FOR investing in Company X."
        *   **Antithesis:** "Build the strongest possible, evidence-based case AGAINST investing in Company X."
    *   Generate an initial `ResearchPlan` for each mission and invoke the two parallel **Research Agent** jobs.

**4.2. Research Agent**
The analytical core of the framework. Thesis and Antithesis agents share the same architecture but operate independently.

*   **Cognitive Loop for each Research Step:**
    1.  **Assess Goal:** Analyze the next step in its `ResearchPlan`.
    2.  **Check for Direct Data:** Determine if an available tool can directly provide the required evidence.
    3.  **Handle Data Gaps (Deductive Proxy Framework):**
        *   If direct data is unavailable, identify and log the `DataGap`.
        *   Formulate a `ProxyHypothesis`: a logical chain from the unobservable claim to an observable, measurable data proxy.
        *   Adapt the `ResearchPlan` to now focus on validating this new proxy.
    4.  **Select Tool & Formulate Query:** Choose the best tool and formulate the precise query to gather the evidence (for either the direct goal or the proxy).
    5.  **Act & Analyze:** Execute the query and parse the results.
    6.  **Record & Justify:** Meticulously log the findings, the tools used, and the complete reasoning (including any proxy hypotheses) in the `ResearchPlan` and `EvidenceDossier`.

**4.3. The Evidence Dossier**
The central data artifact ensuring transparency and auditability.

*   **Structure:** A structured document containing the agent's mission, the full research plan (with justifications), a list of all evidence items, and a summary of findings.

**4.4. Synthesis Agent**
A specialized, stateless agent that creates the final report.

*   **Core Prompt:** "You will be given two approved evidence dossiers: a Thesis and an Antithesis. Your task is to write a single, balanced executive summary. Your summary must: 1) State the core thesis argument. 2) State the core antithesis argument. 3) Explicitly highlight key points of conflict and contradiction. 4) Provide a final, nuanced assessment based *only* on the evidence and citations present in the provided dossiers."

---

#### **5. Data Models and Interfaces**

**5.1. `ResearchPlan` Model (with Deductive Proxy)**
The plan is a living document that captures the agent's reasoning.
```json
{
  "plan_id": "plan-thesis-123",
  "steps": [
    {
      "step_id": "step-001",
      "description": "Assess the durability of the company's competitive moat.",
      "status": "COMPLETED",
      "data_gap_identified": "Direct measurement of 'moat durability' is not possible.",
      "proxy_hypothesis": {
        "unobservable_claim": "The company possesses a durable moat based on brand loyalty and pricing power.",
        "deductive_chain": "If a strong moat exists, the company can raise prices without losing customers, leading to sustained high profitability.",
        "observable_proxy": "Consistently high and stable Gross Profit Margins (>70%) for the last 10 years, relative to peers."
      },
      "tool_used": "financial_database_tool",
      "tool_selection_justification": "The observable proxy requires historical financial data, making this the correct tool.",
      // ... other fields
    }
  ]
}
```

**5.2. `EvidenceItem` Model**
Each piece of evidence is a structured object, linking a finding back to its source.
```json
{
  "evidence_id": "evi-001",
  "finding": "Gross margins have remained stable at an average of 78% from 2013-2023.",
  "source_document_id": "doc-10K-2023",
  "source_location": "Page 45, 'Selected Financial Data'",
  "tags": ["profitability", "moat-proxy"]
}
```

---

#### **6. Core Workflow: Investment Analysis Example**

1.  **User Query:** "Evaluate the long-term investment case for Nike (NKE)."
2.  **Orchestrator** creates two missions:
    *   **Thesis:** "Build the case that Nike's brand moat ensures long-term growth."
    *   **Antithesis:** "Build the case that Nike's moat is threatened by competition and shifting consumer tastes."
3.  **Thesis Research Agent** hypothesizes that a strong brand (unobservable) can be proxied by sustained pricing power (observable as high gross margins). It queries financial data and finds evidence of historically strong margins.
4.  **Antithesis Research Agent** hypothesizes that an eroding moat (unobservable) can be proxied by rising inventory levels and increased marketing spend as a percentage of sales (observable). It queries financial statements and finds that both metrics have been trending upwards recently.
5.  **Human Verifier** opens the **Dialectical Review Interface**. They see the Thesis dossier's argument (strong margins = strong moat) next to the Antithesis dossier's argument (rising inventory/marketing = weakening moat).
6.  The verifier uses the **Structured Verification Protocol** to assess the logic of each proxy. They find both lines of reasoning to be plausible and approve both dossiers.
7.  The **Synthesis Agent** receives both approved dossiers. It generates a report stating: "While Nike's historical profitability provides strong evidence for a durable brand moat (Thesis Dossier), recent trends in inventory and marketing costs suggest emerging competitive pressures that must be monitored (Antithesis Dossier)."

---

#### **7. Human-in-the-Loop (HITL) UI/UX**

The user interface is designed to facilitate, not just enable, human oversight.

**7.1. The Dialectical Review Interface**
A two-column layout presenting the Thesis and Antithesis dossiers side-by-side, allowing for direct comparison of their plans, evidence, and conclusions.

**7.2. The Structured Verification Protocol**
To ensure deep engagement, the "Approve" button for each dossier is only enabled after the human verifier completes a mandatory checklist in the UI:

*   [ ] **Review Summary:** I have read the agent's summary of findings.
*   [ ] **Validate Proxy Logic:** For steps involving a `ProxyHypothesis`, I have assessed the deductive chain and find it to be a sound and relevant line of reasoning.
*   [ ] **Spot-Check Evidence:** I have spot-checked at least three `EvidenceItems` against their original sources.
*   [ ] **Audit Reasoning:** I have reviewed the `ResearchPlan` and the agent's justifications and find the overall process logical.

---

#### **8. Implementation Considerations**

*   **Job Orchestration:** The parallel execution of research jobs will be managed by a robust background task framework (e.g., Celery, Dramatiq) or a dedicated workflow engine.
*   **State Management:** The state of each research job (and its associated dossiers) will be tracked in a dedicated database to ensure resilience.
*   **LLM Integration:** The system will use a standardized interface to interact with various LLMs, allowing for model upgrades or swaps with minimal code changes.

---

#### **9. Conclusion**

AR v3.0 represents a significant step towards creating truly analytical AI. By combining a bias-resistant **Dialectical Research Architecture** with a resourceful **Deductive Proxy Framework**, the system can navigate the complexities and ambiguities of real-world decision-making. It delivers not just answers, but transparent, auditable, and adversarially stress-tested reasoning, providing decision-makers with the quiet confidence that comes from a deep and intellectually honest understanding of their problem.