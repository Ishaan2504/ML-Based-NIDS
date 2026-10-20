# Architecture Decision Records (ADRs)

This document records the foundational architectural decisions, rationale, and tradeoffs established for the Sentinel NIDS project.

---

### ADR-001: Offline-First Forensic Analysis Scope
- **Status**: Accepted
- **Context**: Real-time live network sniffing requires root/administrator privileges, introduces potential eavesdropping liabilities, and poses security and privacy risks with live corporate/campus traffic.
- **Decision**: Restrict the NIDS scope strictly to offline, recorded network flow analysis (e.g. CIC-IDS2017 bidirectional flow CSVs).
- **Consequences**:
  - Safe, deterministic, and fully reproducible experimentation.
  - Zero live packet sniffing dependencies (e.g. libpcap/winpcap not required).
  - Eliminates legal interception and eavesdropping concerns.

---

### ADR-002: Leakage-Aware Contiguous Block Splitting
- **Context**: Naive random train-test splitting across tabular network flows leads to massive data leakage. Flows from the same attack burst or communication session appear in both train and test partitions, inflating reported accuracy.
- **Decision**: Partition datasets into Train (60%), Validation (20%), and Test (20%) using contiguous blocks or day-aware partitions without shuffling across boundaries.
- **Consequences**:
  - Eliminates temporal cross-talk and shortcut learning.
  - Test metrics reflect true generalization performance on unseen traffic bursts.

---

### ADR-003: Validation-Only Threshold Tuning & Model Freezing
- **Context**: Optimizing classification probability thresholds on the test set leads to optimistic performance estimates.
- **Decision**:
  - All feature scaling, imputation, and encoding transformers are fitted strictly on the Train set.
  - Decision threshold tuning (balancing Precision, Recall, and False Alarm Rate) is conducted solely on the Validation split.
  - The model bundle is serialized and locked with a cryptographic hash before evaluating the Test split.
- **Consequences**:
  - Test partition is evaluated strictly once.
  - Results conform to rigorous academic and peer-review benchmarks.

---

### ADR-004: Decoupled FastAPI and Modern React SOC UI
- **Context**: NIDS tools need to be usable by security analysts while also offering automated machine-to-machine inference.
- **Decision**: Expose the model through an asynchronous **FastAPI** REST microservice and interface it with a **React 19 + TypeScript + Tailwind 4** SOC terminal dashboard.
- **Consequences**:
  - Decoupled frontend can be deployed independently across desktop and web environments.
  - API provides clear endpoints (`/predict`, `/predict/batch`, `/explain`) for external SIEM integration.

---

### ADR-005: Storage Format & Serialization
- **Context**: Raw CSVs are slow to parse and consume excessive memory.
- **Decision**: Convert sanitized interim datasets to Snappy-compressed Parquet files and serialize fitted pipelines via Joblib bundles (`models/bundle.joblib`).
- **Consequences**:
  - 10x speedup in data loading during pipeline execution.
  - Atomic, self-contained model artifacts containing both preprocessing transformers and trained estimators.

### ADR-006: Technical specification is authoritative
- **Date**: 2026-10-20
- **Status**: Accepted
- **Context**: The repository's earlier README and ADR-004 describe a React dashboard, while the attached technical specification defines a Streamlit dashboard and a phased implementation.
- **Decision**: Follow the attached technical specification for new behavior. Preserve the existing React dashboard during the earlier data-pipeline phases; replace or remove it only in Phase 6 after Phases 1–5 pass their acceptance checks.
- **Reason**: The specification is the current user-provided requirement, and its phase gates require a working data and inference foundation before dashboard implementation.
