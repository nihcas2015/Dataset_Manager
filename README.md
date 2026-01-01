# Dataset Manager
An Intelligent End-to-End Dataset Collection and Preprocessing System

## 📌 Overview
Dataset Manager is a comprehensive, intelligent system designed to handle the complete lifecycle of datasets — from discovery and generation to preprocessing and preparation for machine learning workflows.

The system provides two primary modules:
1. Dataset Collector
2. Dataset Preprocessor

Together, these modules enable users to efficiently acquire, generate, and preprocess datasets using natural language interactions and AI-assisted automation.

---

## 🎯 Key Objectives
- Simplify dataset discovery from multiple online sources
- Provide automated dataset downloading and retrieval
- Generate synthetic datasets when suitable data is unavailable
- Enable natural-language-driven data preprocessing
- Create a unified platform for complete dataset management

---

## 🧠 System Architecture

### 1️⃣ Dataset Collector
The Dataset Collector helps users obtain datasets using two sub-modules:

#### 🔹 Dataset Searcher
- Accepts a natural language dataset query from the user
- Searches across:
  - Public dataset platforms (e.g., Kaggle)
  - Government and organization portals (e.g., data.gov)
  - Open research and data repositories
- Identifies relevant datasets matching the query
- Attempts automatic dataset download
- If automatic download is not possible:
  - Retrieves and provides the dataset URL
  - Allows the user to manually download the dataset

#### 🔹 Dataset Generator
- Activated when the user is not satisfied with available datasets
- Uses an LLM (LLaMA) to generate synthetic/mock datasets
- Creates structured data based on the user’s dataset description
- Useful for prototyping, testing, and experimentation

---

### 2️⃣ Dataset Preprocessor
The Dataset Preprocessor prepares datasets for analysis and machine learning.

- Asks the user for the local dataset storage location
- Accepts preprocessing instructions in natural language
- Examples of preprocessing steps:
  - Handling missing values
  - Encoding categorical variables
  - Feature scaling and normalization
  - Removing duplicates or outliers
  - Column selection and transformation
- Uses cosine similarity to match user instructions with predefined preprocessing operations
- Applies preprocessing steps sequentially as requested
- Outputs a clean, ready-to-use dataset

---

## 🔄 End-to-End Workflow
1. User selects Dataset Collector or Dataset Preprocessor
2. For Dataset Collector:
   - Enter dataset query
   - Search datasets online
   - Download dataset or retrieve source URL
   - Optionally generate synthetic data
3. For Dataset Preprocessor:
   - Provide dataset location
   - Describe preprocessing steps in natural language
   - System interprets and executes preprocessing
4. Final dataset is ready for analysis or modeling

---

## ⚙️ Tech Stack
- Programming Language: Python
- LLM: LLaMA (via local or API-based inference)
- Data Processing: Pandas, NumPy
- Text Similarity: Cosine Similarity
- Dataset Sources: Kaggle, data.gov, open data repositories

---

## 🚀 Key Features
- Intelligent dataset search and retrieval
- Automated and manual dataset download support
- Synthetic dataset generation
- Natural language preprocessing instructions
- Step-wise preprocessing execution
- Unified dataset management platform

