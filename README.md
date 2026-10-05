# SmartHire ATS

An AI-powered Applicant Tracking System (ATS) that analyzes resumes against job descriptions, evaluates resume quality, validates skills, generates ATS scores, and provides intelligent career insights.

SmartHire is designed for students, job seekers, and developers who want to understand how well their resume matches a target role and improve their chances of getting shortlisted.

---

## 🌐 Live Demo

**Web Application:**  
https://your-vercel-domain.vercel.app/

**GitHub Repository:**  
https://github.com/KalyanSai956/SmartHire_ATS

> Replace the Vercel URL above with your actual deployed frontend URL.

---

## 🏗️ Architecture

SmartHire ATS follows a modular full-stack architecture connecting the React/Vite frontend, FastAPI backend, Supabase services, NLP/AI engines, Redis caching, and external LLM providers.

<p align="center">
  <img
    src=".screenshots/smarthire_ats_architecture.png"
    alt="SmartHire ATS Architecture"
    width="100%"
  />
</p>

### Architecture Flow

```text
React + Vite
     │
     ├── Supabase Authentication
     │        │
     │        └── JWT
     │
     ▼
FastAPI Backend
     │
     ├── API Routes
     │
     ├── Resume Scoring
     ├── Job Matching
     ├── Resume Search / RAG
     └── PDF Reports
     │
     ├───────────────┬───────────────┐
     ▼               ▼               ▼
 NLP Engine       Supabase         Redis
 spaCy            PostgreSQL       Cache
 Sentence         Database         Rate Limits
 Transformers
     │
     ▼
LLM Gateway
     │
     ├── Groq
     ├── OpenAI
     ├── Google
     └── Anthropic


## 📸 Screenshots

### Landing Page

![SmartHire Landing Page](./screenshots/landing.png)

### Dashboard

![SmartHire Dashboard](./screenshots/dashboard.png)

### Resume Analysis

![SmartHire Resume Analysis](./screenshots/analysis.png)

### Jobs

![SmartHire Resume Analysis](./screenshots/jobs.png)

### ATS Results

![SmartHire ATS Results](./screenshots/results.png)

### AI Gateway

![SmartHire Interview Preparation](./screenshots/aigateway.png)


## ✨ Features

### 🤖 AI-Powered Resume Analysis

- AI-powered resume analysis
- Resume text extraction
- Structured resume profile generation
- Skills extraction
- Experience analysis
- Project analysis
- Resume quality evaluation
- Detailed resume feedback

### 📊 Advanced ATS Scoring

SmartHire evaluates resumes using multiple dimensions instead of relying only on keyword matching.

- Overall ATS Score
- Job Description Match
- Keyword Match
- Semantic Match
- Skills Match
- Experience Match
- Project Match
- Resume Quality
- Missing Keywords
- Matched Keywords
- Skills Gap

### 🧠 Semantic Resume Matching

SmartHire uses NLP and semantic embeddings to understand the relationship between a resume and a job description.

This helps identify relevant experience and skills even when the exact keywords are not present.

### 💼 Job Description Intelligence

Analyze job descriptions to identify:

- Role information
- Required skills
- Preferred skills
- Job-specific requirements
- Resume-to-JD compatibility

### 📄 Resume Quality Engine

Resume quality is evaluated across multiple categories:

- Contact Information
- Structure
- Experience
- Projects
- Skills
- Content Quality

### 🔎 Skill Validation

SmartHire analyzes skills mentioned in a resume and provides validation information including:

- Validated skills
- Unvalidated skills
- Total skills
- Validated skill count
- Validation percentage

### 📝 Detailed Feedback

The system provides actionable feedback to help candidates improve:

- Resume content
- Missing skills
- Missing keywords
- Project relevance
- Job-description alignment
- Overall resume quality

### 📚 Analysis History

Users can access previously analyzed resumes and maintain their analysis history.

### 📥 PDF Reports

Generate downloadable PDF reports containing resume analysis results.

### 🔐 Authentication

SmartHire includes authenticated user workflows and user-specific analysis history.

### 🔑 BYOK AI Providers

SmartHire supports Bring Your Own Key (BYOK) workflows for supported AI providers.

### ⚡ Redis

Redis is used for application caching, quota controls, and rate-limiting infrastructure.

### 🧩 Resume Semantic Indexing

SmartHire includes resume semantic indexing using embeddings, providing a foundation for retrieval-augmented career and resume intelligence.

### 🐳 Docker

The backend can be run using Docker and Docker Compose.

---
```
