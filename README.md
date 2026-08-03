# TechCareer.ai - AI-Powered Career Assistant & Intelligent Job Marketplace

> **Live Application URL:** [https://tech-career-ai.vercel.app](https://tech-career-ai.vercel.app)

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [Tech Stack](#tech-stack)
4. [Key Architecture & End-to-End Workflow](#key-architecture--end-to-end-workflow)
5. [Local Development & Setup Guide](#local-development--setup-guide)
6. [Future Roadmap](#future-roadmap)
7. [License](#license)

---

## Project Overview

**TechCareer.ai** is an end-to-end, AI-driven career platform and intelligent job marketplace designed to bridge the gap between IT professionals and career opportunities. Built with a robust full-stack architecture, advanced Natural Language Processing (NLP), Large Language Models (LLMs), and vector search capabilities, the platform automates job aggregation from top career portals, processes and classifies listings using machine learning models, and provides an interactive AI chatbot companion for resume analysis, interview coaching, and semantic job matching.

---

## Key Features

* **Automated Job Aggregation:** Daily, anti-bot bypassed scraping from 5 major career portals.
* **AI Chatbot Companion:** Gemini-powered assistant for interactive CV reviews, mock interviews, and career mentoring.
* **Semantic Resume Matching:** Upload a CV (PDF) to instantly discover matching jobs using high-dimensional vector similarity.
* **Market Intelligence Dashboard:** Real-time visual analytics of the IT job market trends.
* **Interactive Career Galaxy Map:** A 2D UMAP-based visualization clustering the tech professional landscape.

---

## Tech Stack

* **Frontend:** React, Axios
* **Backend:** FastAPI, Python 3.10+, Uvicorn, Slowapi (Rate Limiting)
* **AI & Machine Learning:** Google Gemini API (`gemini-3.5-flash`), Scikit-Learn, Optuna, UMAP, HDBSCAN, Sentence Transformers
* **Database:** ChromaDB (Vector Database)
* **Data Collection:** Playwright, Patchright
* **Deployment & DevOps:** AWS EC2 (Ubuntu), Cron Jobs, Vercel

---

## Key Architecture & End-to-End Workflow

### 1. Web Scraping & Data Collection Pipeline
To build a comprehensive dataset of active technology and software career opportunities, a custom automated scraping framework was developed utilizing Python alongside **Playwright** and **Patchright**. 
* **Target Platforms:** Data is dynamically extracted from 5 major career portals: *Kariyer.net, LinkedIn, Indeed, TechCareer.net,* and *Youthall*.
* **Anti-Bot Bypass Strategies:** Advanced anti-bot measures, rate limits, and Cloudflare challenges present on enterprise career sites were bypassed using stealth browser contexts, randomized user-agent rotation, human-like interaction delays, and proxy/session management.
* **Storage:** All raw and extracted job postings are systematically ingested and saved locally in structured **JSONL (JSON Lines)** format for scalable downstream data engineering.

### 2. Data Cleaning & Preprocessing
Following extraction, the raw JSONL files undergo a rigorous data normalization pipeline:
* **Aggregation & De-duplication:** Multiple platform datasets are merged, removing redundant postings and standardizing text encodings.
* **Noise Reduction & Filtering:** Irrelevant positions (e.g., non-tech roles, service jobs) are filtered out via automated keyword blacklists.
* **Field Standardization:** Job attributes such as locations, work models (Remote, Hybrid, On-site), experience tiers, and job types are normalized into clean, unified schemas.

### 3. Machine Learning Model Training & Optimization
The pipeline features three distinct machine learning models designed to enrich metadata and understand listing semantics:
* **Model 1 (Supervised - Experience Level Classification):** Predicts and classifies the required seniority level (e.g., Junior, Mid-Level, Senior, Lead) based on job descriptions. Various classification algorithms were tested, with the best-performing model optimized using **Optuna** for hyperparameter tuning.
* **Model 2 (Supervised - Domain Categorization):** Automatically categorizes job postings into technical domains (e.g., Software Engineering, Data Science, DevOps, Cybersecurity, AI/ML) using optimized ensemble classifiers tuned via **Optuna**.
* **Model 3 (Unsupervised - Semantic Similarity & Clustering):** Analyzes relationships between job postings. This model incorporates **UMAP** for dimensionality reduction and **HDBSCAN** for density-based clustering to map out the professional landscape and group related technological domains.

### 4. Consolidated Prediction Pipeline & Embedding Generation
* **Unified Inference (`predict.py`):** The three standalone models are consolidated into a unified prediction script that processes raw listings into a rich, fully-labeled master dataset.
* **RAG Architecture & Vector Database:** Job texts and enriched metadata are transformed into high-dimensional vector embeddings using Sentence Transformers (`paraphrase-multilingual-MiniLM-L12-v2`). These vectors are ingested and persisted in a high-performance **ChromaDB** vector database to enable real-time Retrieval-Augmented Generation (RAG) and semantic similarity searches.

### 5. Automated Cloud Pipeline (AWS Cron Automation)
* The entire data collection, scraping, model prediction, and database update pipeline is fully automated.
* Deployed on an **AWS EC2 Ubuntu instance**, cron jobs execute the end-to-end pipeline daily at scheduled hours, keeping the job market database completely up-to-date without manual intervention.

### 6. AI Chatbot Engine (`chatbot_engine.py`) powered by Google Gemini
* **LLM Integration:** Powered by Google's `gemini-3.5-flash` model via the official `google-genai` SDK.
* **Capabilities:** 
  * **CV Analysis & Parsing:** Extracts skills and computes semantic match percentages against live database listings.
  * **Intelligent Job Matching:** Filters and recommends positions tailored specifically to an uploaded resume.
  * **Interactive Interview Simulation & Career Advice:** Acts as a career mentor, offering mock interview questions, resume improvement tips, and multilingual streaming chat responses.

### 7. Backend (FastAPI) & Frontend (React) Integration
* **FastAPI Backend:** A high-performance asynchronous REST API built with FastAPI, handling vector search queries (`/api/jobs/search`), dynamic filter generation (`/api/jobs/filters`), dashboard analytics (`/api/dashboard/stats`), CV parsing (`/api/cv/upload`), PCA data generation for visual maps (`/api/galaxy-map`), and streaming LLM chat endpoints (`/api/chat`). Rate-limiting (`slowapi`) and CORS middleware ensure production security.
* **React Frontend:** A modern, responsive user interface communicating seamlessly with the backend API via Axios. Features include real-time filtering, interactive charts, a visual career galaxy map, saved job tracking, and an embedded AI assistant drawer.

---

## Local Development & Setup Guide

To run this project locally on your machine, follow these steps:

### Prerequisites
* Python 3.10+
* Node.js & npm (for frontend deployment if running locally)
* Git

### 1. Clone the Repository
```bash
git clone https://github.com/irmakoznrgz/AI-Tech-Career-Assistant.git
cd tech-talent-scraper
2. Backend Setup & Dependencies
Create and activate a virtual environment:

Bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
Install the required Python packages:

Bash
pip install -r requirements.txt
3. Environment Configuration
Create a .env file in the root directory and add your Google Gemini API key:

Code snippet
GEMINI_API_KEY=your_google_gemini_api_key_here
4. Initialize Vector Database
Ensure your ChromaDB data files are present in data/chroma_db, or build the database using your local scraper/prediction pipeline:

Bash
python src/build_vector_db.py
5. Run the FastAPI Server
Start the backend server using Uvicorn:

Bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
The API will be available at http://localhost:8000, and interactive Swagger documentation at http://localhost:8000/docs.

Future Roadmap
[ ] **Expanded Data Sources:** Integrate additional local and international tech job boards to broaden the career opportunity pool.

[ ] **Conversational Job Search:** Enable users to query, filter, and discover job listings directly through natural language interactions within the AI Chatbot.

[ ] **User Accounts & Profiles:** Implement a comprehensive authentication system allowing users to create personalized profiles, save favorite jobs, and persist chat history across sessions.

License
This project is developed as an advanced AI career platform. Feel free to fork, contribute, or adapt for personal and professional use.