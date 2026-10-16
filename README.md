# 🛡️ Sentinel NIDS: ML-Based Network Intrusion Detection System

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React 19" />
  <img src="https://img.shields.io/badge/TypeScript-5.7-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-v4-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white" alt="Tailwind CSS v4" />
  <img src="https://img.shields.io/badge/Dataset-CIC--IDS2017-orange?style=for-the-badge" alt="Dataset" />
</p>

---

## 📌 Executive Summary

**Sentinel NIDS** is an enterprise-oriented, dataset-driven Network Intrusion Detection System (NIDS) designed for offline, forensic-grade analysis of bidirectional network flow records from the benchmark **CIC-IDS2017** dataset.

The system combines statistical machine learning classifiers (**Logistic Regression**, **Random Forest**, **XGBoost**, and **Isolation Forest**) with strict, leakage-aware experimental methodologies. It provides automated detection of malicious traffic, maps anomalous flows to standardized threat families, exposes inference via a high-performance **FastAPI** backend, and delivers real-time investigative telemetry through an interactive, terminal-themed **SOC (Security Operations Center) React Dashboard**.

> [!IMPORTANT]
> **Academic & Research Integrity Notice**:
> This project follows strict scientific evaluation principles. Train/validation/test splits are constructed to eliminate data leakage. Final benchmark metrics are derived exclusively from frozen models evaluated on the held-out test split. Uncalibrated scores are treated as statistical model outputs rather than verified ground truth.
>
> **Current Status**: Core architecture, React SOC frontend, API specifications, and pipeline scaffolds are established. Model benchmarking artifacts are generated via the reproducible pipeline under `reports/`.

---

## 📑 Table of Contents

- [Executive Summary](#-executive-summary)
- [System Architecture](#-system-architecture)
- [Key Features](#-key-features)
- [Detection Models & Attack Taxonomy](#-detection-models--attack-taxonomy)
- [Security Operations Center (SOC) Frontend](#-security-operations-center-soc-frontend)
- [API Service Specification](#-api-service-specification)
- [Methodology & Leakage Prevention](#-methodology--leakage-prevention)
- [Repository Structure](#-repository-structure)
- [Installation & Setup](#-installation--setup)
- [Pipeline Execution](#-pipeline-execution)
- [Mini-Project Assessment & Rubric Alignment](#-mini-project-assessment--rubric-alignment)
- [Ethical, Privacy & Security Disclaimers](#-ethical-privacy--security-disclaimers)
- [References & Citation](#-references--citation)

---

## 🎯 Scope & Boundaries

- **Validated Flow Analysis**: Designed specifically for bidirectional flow data extracted from packet captures (e.g. CICFlowMeter output for CIC-IDS2017).
- **Offline & Privacy-Preserving**: Operates in isolated, local execution environments without sniffing live network interfaces or exfiltrating data.
- **Reproducible Pipeline**: Multi-stage data processing pipeline ensuring strict separation of training, validation, and test sets.
