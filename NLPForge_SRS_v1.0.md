# NLPForge
## AI-Powered NLP Dataset Generator & Semantic Search Platform
### Software Requirements & Design Specification (SRS)

**Document Version:** 1.0  
**Date:** June 2026  
**Prepared For:** AI Engineers / API Developers / QA Automation Teams  
**Status:** Draft for Development Planning  

---

## Table of Contents
1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [Functional Modules & Requirements](#3-functional-modules--requirements)
4. [Two-Stage Retrieval Logic (Detailed Workflow)](#4-two-stage-retrieval-logic-detailed-workflow)
5. [System Architecture Overview](#5-system-architecture-overview)
6. [Roles & Permissions Matrix](#6-roles--permissions-matrix)
7. [Development Roadmap / Phased Delivery](#7-development-roadmap--phased-delivery)
8. [Sample Acceptance Criteria (Key Flows)](#8-sample-acceptance-criteria-key-flows)
9. [Future Enhancements (Out of V1 Scope)](#9-future-enhancements-out-of-v1-scope)

---

## 1. Introduction

### 1.1 Purpose
This document defines the functional and non-functional requirements, system architecture, and feature scope for an enterprise-grade AI-powered platform called **NLPForge**.
NLPForge bridges the gap between natural language and API testing. The system enables users to describe test scenarios in plain English, generating structured, executable API test cases by utilizing a two-stage retrieval pipeline with LLM-powered semantic understanding.

### 1.2 Project Background
Traditional API testing requires writing complex scripts and manually determining API endpoints and payload structures. Translating test scenarios from natural language specifications into executable API calls is time-consuming and error-prone. NLPForge automates this process by processing queries through semantic embedding, vector similarity search, neural re-ranking, and slot extraction to map natural language directly to API templates.

### 1.3 Scope
The system covers the end-to-end flow of NLP-based API test generation: API template definition, synthetic dataset generation across multiple LLM providers, dataset embedding and storage in vector databases, and a real-time semantic search pipeline using a two-stage retrieval mechanism (Vector Similarity + FlashRank Re-ranking) followed by LLM-powered slot extraction. It also includes comprehensive analytics and enterprise security features.
Out of scope for Version 1.0: direct execution of the generated API calls against target environments (it outputs the structured test cases, but execution is delegated to external tools like Postman or automated test runners).

### 1.4 Intended Audience
*   **API Developers / QA Automation Engineers** (primary users creating templates and running queries)
*   **System Administrators** (configuring models, LLM providers, and managing system health)
*   **Project Managers** (reviewing analytics, template approvals)
*   **Development team** (for build reference)

### 1.5 Definitions, Acronyms & Abbreviations

| Term | Description |
| :--- | :--- |
| **LLM** | Large Language Model (e.g., GPT-4, Claude, Gemini, Llama) |
| **Embedding** | A mathematical vector representation of text used to measure semantic similarity |
| **HNSW** | Hierarchical Navigable Small World, an algorithm used for approximate nearest neighbor search in vector databases |
| **Cross-Encoder** | A neural network model that processes a pair of texts together to produce a highly accurate relevance score (used in re-ranking) |
| **RAG** | Retrieval-Augmented Generation |
| **Slot Extraction** | The process of pulling specific parameter values out of a natural language query based on a defined schema |

---

## 2. Overall Description

### 2.1 Product Perspective
NLPForge is a standalone web application featuring a Next.js App Router frontend, a FastAPI asynchronous backend, PostgreSQL for relational data, and Redis Stack for vector storage and caching. The system heavily leverages AI/ML services, incorporating Ollama for local embedding and inference, FlashRank for cross-encoder re-ranking, and integrates with 8 major Cloud LLM providers. It is deployed as a containerized stack via Docker Compose.

### 2.2 User Classes and Characteristics

| Role | Description | Key Permissions |
| :--- | :--- | :--- |
| **System Admin** | Platform administrator | Manage all LLM configs, embedding models, system-wide settings, user roles |
| **Expert / Reviewer** | Senior QA/Developer | Approve/reject API templates, review generated datasets |
| **Standard User** | Standard developer/tester | Create templates (draft), generate datasets, query the semantic search engine |

### 2.3 Operating Environment
*   **Frontend:** Modern browsers (Chrome, Firefox, Edge, Safari) on desktop
*   **Backend & Infrastructure:** Docker-ready environment with minimum 8GB RAM (16GB+ recommended for local LLM inference)
*   **Third-Party AI:** Integration with external APIs (OpenAI, Gemini, Anthropic, etc.) or local Ollama servers

### 2.4 Design and Implementation Constraints
*   **Performance:** The semantic search pipeline (Stage 1 + Stage 2 + Extraction) must respond in near real-time.
*   **Security:** API keys for LLMs must be encrypted at rest using Fernet encryption. Rate limiting (100 req/min per IP) must be strictly enforced.
*   **Data Isolation:** Multi-tenant architecture requires full isolation of user data, templates, and datasets.

### 2.5 Assumptions and Dependencies
*   Users must configure valid API keys for cloud LLMs or have local Ollama instances running to utilize generation and extraction features.
*   The system relies on Redis Stack 7.2+ for its HNSW vector search capabilities.

---

## 3. Functional Modules & Requirements

### 3.1 Authentication & Security
| ID | Requirement |
| :--- | :--- |
| FR-1.1 | User registration and login with email/password (bcrypt hashing) |
| FR-1.2 | Email verification via OTP |
| FR-1.3 | Secure session management with JWT tokens |
| FR-1.4 | Encryption at rest for user-provided LLM API keys |
| FR-1.5 | Role-based access control and multi-tenant data isolation |
| FR-1.6 | Audit logging of all critical actions and queries |

### 3.2 Template Management
| ID | Requirement |
| :--- | :--- |
| FR-2.1 | Create API templates with Name, HTTP Method, Endpoint URL, Parameters |
| FR-2.2 | Enforce minimum 500-word descriptions and 3+ sample utterances per template |
| FR-2.3 | Template categorization and domain tagging |
| FR-2.4 | Support draft, review, and approved states with version history |

### 3.3 Dataset Generation
| ID | Requirement |
| :--- | :--- |
| FR-3.1 | Generate synthetic datasets using selected LLM providers based on an approved template |
| FR-3.2 | Configure data distribution: 70% valid, 20% edge cases, 10% extreme scenarios |
| FR-3.3 | Export generated datasets in CSV and JSON formats |
| FR-3.4 | Display progress of background generation tasks |

### 3.4 Embedding & Vector Storage
| ID | Requirement |
| :--- | :--- |
| FR-4.1 | Support 15+ embedding models via Ollama (e.g., nomic-embed-text) |
| FR-4.2 | Automatically generate embeddings for datasets upon creation or request |
| FR-4.3 | Store embeddings in Redis using HNSW indexing for fast KNN retrieval |
| FR-4.4 | Provide model validation and dimensionality checking |

### 3.5 Semantic Search & Two-Stage Pipeline
| ID | Requirement |
| :--- | :--- |
| FR-5.1 | Accept natural language query input from the user |
| FR-5.2 | **Stage 1:** Execute vector similarity search against Redis to retrieve the top-5 candidate templates |
| FR-5.3 | **Stage 2:** Perform neural cross-encoder re-ranking on the top-5 candidates using FlashRank |
| FR-5.4 | **Extraction:** Use an LLM to extract specific parameters/slots from the user's query based on the top-ranked template |
| FR-5.5 | Output structured JSON containing the selected API endpoint, method, and extracted payload/parameters |

### 3.6 Configuration & Settings
| ID | Requirement |
| :--- | :--- |
| FR-6.1 | Configure LLM providers (OpenAI, Gemini, Anthropic, Grok, DeepSeek, Ollama, HuggingFace, Custom) |
| FR-6.2 | Select default models and adjust parameters (temperature, max tokens) |
| FR-6.3 | Download and configure preferred local embedding models via Ollama |

### 3.7 Analytics Dashboard
| ID | Requirement |
| :--- | :--- |
| FR-7.1 | Track KPIs: Total templates, datasets, embeddings, and query volume |
| FR-7.2 | Visualize intent distribution and query performance metrics |
| FR-7.3 | Monitor embedding model accuracy and retrieval confidence scores |

---

## 4. Two-Stage Retrieval Logic (Detailed Workflow)

The core mechanism mapping plain text queries to API specifications.

### 4.1 Semantic Understanding
When a user inputs a query (e.g., "Authenticate with email admin@test.com and password securepass"), the configured embedding model converts this query into a high-dimensional vector.

### 4.2 Stage 1: Vector Similarity (Fast Recall)
1. The query vector is matched against all stored template vectors in Redis.
2. An HNSW-based K-Nearest Neighbors (KNN) search retrieves the top 5 most similar API templates based on cosine similarity.

### 4.3 Stage 2: Neural Re-ranking (Precision)
3. The original text query and the text of the top 5 candidate templates are paired.
4. A FlashRank Cross-Encoder model (`ms-marco-MiniLM-L-12-v2`) evaluates each pair, producing a highly precise relevance score between 0.0 and 1.0.
5. Candidates are re-ordered based on this score, determining the single best matching API template.

### 4.4 Slot Extraction
6. The best matching template and the original query are sent to the configured LLM.
7. The LLM extracts the relevant variables from the query (e.g., `email="admin@test.com"`, `password="securepass"`) and maps them to the template's required parameters.
8. A final, executable JSON payload is returned to the user.

---

## 5. System Architecture Overview

### 5.1 High-Level Architecture
*   **Frontend Client:** Next.js 16 (React 18, TailwindCSS) providing the user interface.
*   **API Layer:** FastAPI (Python 3.11+) asynchronous REST endpoints.
*   **Service Layer:** 20+ async services handling auth, embedding, multi-model orchestration, dataset generation, ranking, and slot extraction.
*   **AI/ML Services:** Ollama for local embeddings/LLM inference and FlashRank for cross-encoder reranking. External API calls to Cloud LLMs.
*   **Data Layer:** PostgreSQL for structured data (Users, Templates, Audit Logs); Redis Stack for vector embeddings and caching.

### 5.2 Suggested Technology Stack

| Layer | Recommended Technology | Notes |
| :--- | :--- | :--- |
| **Frontend** | Next.js 16, React 18, TailwindCSS | App Router, Server Components |
| **Backend API** | FastAPI, Python 3.11+ | Fully asynchronous, Pydantic validation |
| **Database** | PostgreSQL 15 | Relational integrity via SQLAlchemy/asyncpg |
| **Vector DB** | Redis Stack 7.2 | Fast HNSW KNN vector search |
| **AI Models** | Ollama, FlashRank | Local processing where possible |
| **Cloud LLMs** | OpenAI, Gemini, Claude, etc. | Encrypted API keys |
| **Auth** | JWT, python-jose, bcrypt | Role-based access control |
| **Hosting** | Docker Compose | Containerized ecosystem |

### 5.3 Non-Functional Requirements

| Category | Requirement |
| :--- | :--- |
| **Security** | Encrypted storage for API keys; HTTPS enforced; rate-limiting via SlowAPI |
| **Scalability** | Asynchronous architecture supports high concurrent loads; Redis caching |
| **Availability** | Docker containers configured with health checks and restart policies |
| **Performance** | Sub-second latency for vector retrieval; FlashRank optimized for speed |
| **Auditability** | Complete logging of all queries, generations, and settings changes |

---

## 6. Roles & Permissions Matrix

| Function | Admin | Expert / Reviewer | Standard User |
| :--- | :--- | :--- | :--- |
| **Manage System Settings** | Full | View Only | View Only |
| **Configure LLM Providers** | Full | Full | Own Config Only |
| **Create API Templates** | Full | Full | Draft Only |
| **Approve Templates** | Full | Full | No |
| **Generate Datasets** | Full | Full | Yes (Approved Templates) |
| **Query Engine** | Full | Full | Yes |
| **View System Analytics** | Full | Full | Own Usage Only |

---

## 7. Development Roadmap / Phased Delivery

### Phase 1 — Core Infrastructure & Templates
*   Authentication & Security framework
*   Database & Redis setup
*   API Template Builder with draft/review workflow

### Phase 2 — AI Integration & Datasets
*   LLM Provider configuration & API key encryption
*   Dataset Generation Wizard
*   Local embedding generation via Ollama

### Phase 3 — Semantic Search Engine
*   Stage 1: Redis HNSW vector search implementation
*   Stage 2: FlashRank integration
*   LLM Slot Extraction
*   End-to-End query pipeline

### Phase 4 — Polish & Enterprise Features
*   Analytics Dashboard
*   Audit logging and Rate limiting
*   Docker orchestration and CI/CD pipelines

---

## 8. Sample Acceptance Criteria (Key Flows)

### 8.1 Template Creation
*   Given a user on the Template Builder, when they enter a description under 500 words, the system prevents submission and shows a validation error.

### 8.2 Dataset Generation
*   Given an approved template, when a user requests 100 rows, the system generates exactly 70 valid, 20 edge-case, and 10 extreme-scenario rows as defined.

### 8.3 Semantic Query Matching
*   Given a natural language query, the system successfully extracts parameters defined in the template and returns a valid JSON object matching the template's endpoint structure.

### 8.4 Security
*   Given a compromised database, the attacker cannot read the LLM API keys because they are stored using Fernet encryption.

---

## 9. Future Enhancements (Out of V1 Scope)
*   Direct execution of generated test cases against target APIs within the NLPForge UI.
*   Integration with CI/CD tools (Jenkins, GitHub Actions) for automated test execution.
*   Advanced prompt tuning and few-shot example management for LLMs.
*   Support for importing OpenAPI/Swagger specifications directly into the Template Builder.
*   Collaborative workspaces for teams sharing templates and datasets.

---
*End of Document*
