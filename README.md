<div align="center">

# 🛡️ Phishing URL Detection — End-to-End MLOps Pipeline

**An automated ML system that classifies URLs as phishing or legitimate — built as a complete, production-style MLOps pipeline from data ingestion through cloud deployment.**

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&logoColor=white)](https://www.mongodb.com/atlas)
[![MLflow](https://img.shields.io/badge/MLflow-DagsHub-0194E2?logo=mlflow&logoColor=white)](https://dagshub.com/sgsatpute/phishing-url-detection-mlops.mlflow)
[![AWS](https://img.shields.io/badge/AWS-EC2%20%7C%20S3%20%7C%20ECR-FF9900?logo=amazonaws&logoColor=white)](https://aws.amazon.com/)
[![Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7?logo=render&logoColor=white)](https://phishing-url-detection-mlops.onrender.com/docs)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](#license)

**[🔗 Live API Docs](https://phishing-url-detection-mlops.onrender.com/docs)** · **[📊 MLflow Experiments](https://dagshub.com/sgsatpute/phishing-url-detection-mlops.mlflow)** · **[📁 Repository](https://github.com/sgsatpute/phishing-url-detection-mlops)**

</div>

---

## Table of Contents
1. [Overview](#-overview)
2. [Live Demo](#-live-demo)
3. [Features](#-features)
4. [Tech Stack](#-tech-stack)
5. [Dataset & Features](#-dataset--features)
6. [Pipeline Architecture](#-pipeline-architecture)
7. [Model Performance](#-model-performance)
8. [Deployment](#-deployment)
9. [Quick Start](#-quick-start)
10. [Project Structure](#-project-structure)
11. [Engineering Challenges Solved](#-engineering-challenges-solved)
12. [License](#license)

---

## 🎯 Overview

This project builds a maintainable, production-style pipeline for detecting malicious/phishing websites from their URL characteristics. Rather than a one-off notebook, it's structured as independent, reusable components — ingestion, validation, transformation, and training — with experiment tracking, schema validation, and statistical drift detection built in throughout.

The trained model is served through a FastAPI application supporting both on-demand retraining (`/train`) and real-time inference (`/predict`), containerized with Docker, and deployed to **two independent cloud environments**: a manually-configured AWS stack (IAM → S3 → ECR → EC2) and an automated, GitHub-integrated deployment on Render.

<div align="center">

![Project Architecture](images/architecture.jpg)

</div>

---

## 🚀 Live Demo

| Environment | URL | Notes |
| :--- | :--- | :--- |
| **Render** *(primary)* | **[phishing-url-detection-mlops.onrender.com/docs](https://phishing-url-detection-mlops.onrender.com/docs)** | Stable, always-available. Free tier spins down after inactivity — first request may take 30–60s to wake. |
| **AWS EC2** | Deployed manually via Docker on a `t3.micro` instance | Demonstrates full manual cloud deployment ownership. |

> 💡 **Try it yourself:** open the live docs above, expand `POST /predict`, upload `valid_data/test.csv`, and hit Execute. You'll get back an HTML table with a `predicted_column` — `1.0` = legitimate, `0.0` = phishing.

---

## ✨ Features

| | |
|---|---|
| 🧩 **Component-based pipeline** | Ingestion, validation, transformation, and training are independent, testable modules orchestrated into one pipeline |
| 📈 **Data drift detection** | Schema validation + Kolmogorov–Smirnov statistical test catches distribution shifts before they reach the model |
| 🧪 **Experiment tracking** | Every training run — hyperparameters, F1, precision, recall — logged to MLflow via DagsHub |
| ☁️ **Automated artifact sync** | Trained models, preprocessors, and reports pushed to AWS S3 after every run |
| 🔌 **REST API** | FastAPI service with `/train` and `/predict`, plus interactive Swagger docs out of the box |
| 🐳 **Dual cloud deployment** | Docker image deployed manually to AWS EC2 via ECR *and* automatically to Render via GitHub integration |

---

## 🛠️ Tech Stack

<div align="center">

| Category | Tools |
| :--- | :--- |
| **API Layer** | FastAPI · Uvicorn |
| **ML / Data** | Scikit-learn · Pandas · NumPy |
| **Data Store** | MongoDB Atlas |
| **Experiment Tracking** | MLflow via DagsHub |
| **Containerization** | Docker |
| **Cloud Storage** | AWS S3 |
| **Cloud Hosting** | AWS EC2 · AWS ECR · Render |
| **Version Control** | Git · GitHub |

</div>

---

## 📊 Dataset & Features

The model is trained on **11,055 URL records**, each described by 30 lexical, domain-based, and page-level features that together signal whether a URL is likely to be malicious.

<div align="center">

![URL Features](images/url_features.jpg)

</div>

**Key features used:**

| Feature | What it captures |
| :--- | :--- |
| `having_IP_Address` | Whether the URL uses a raw IP instead of a domain name |
| `URL_Length` | Overall URL length — longer URLs are more often suspicious |
| `Shortining_Service` | Whether a URL shortener (e.g. bit.ly) was used |
| `having_At_Symbol` | Presence of "@", which can mask the real destination domain |
| `SSLfinal_State` | Validity/trustworthiness of the SSL certificate |
| `Domain_registeration_length` | How long the domain has been registered |
| `age_of_domain` | How long the domain has existed |
| `web_traffic` | Site traffic rank as a proxy for legitimacy |
| `Google_Index` | Whether the page is indexed by Google |

---

## 🏗️ Pipeline Architecture

<div align="center">

![Pipeline Workflow Overview](images/pipeline_workflow_diagram.png)

</div>

### 1️⃣ Data Ingestion
Pulls raw records from MongoDB Atlas, splits into train/test sets, stores as versioned artifacts.

<div align="center">

![Data Ingestion Flow](images/data_ingestion_flow.png)

</div>

### 2️⃣ Data Validation
Validates data against `data_schema/schema.yaml` (column count, types) and runs a Kolmogorov–Smirnov test to detect statistical drift between train and test distributions.

<div align="center">

![Data Validation Flow](images/data_validation_flow.png)

</div>

### 3️⃣ Data Transformation
Missing values imputed with `KNNImputer`; features passed through a preprocessing pipeline; results saved as NumPy arrays.

<div align="center">

![Data Transformation Flow](images/data_transformation_flow.png)

</div>

### 4️⃣ Model Training
Multiple candidate models trained via `GridSearchCV`. Every run — params, F1, precision, recall — logged to MLflow (tracked live on DagsHub). Best model + preprocessor persisted.

<div align="center">

![Model Training Flow](images/model_training_flow.png)

</div>

### 5️⃣ Artifact Sync
Datasets, validation reports, and trained artifacts synced automatically to an S3 bucket after every run.

### 6️⃣ Serving
The best model is loaded by FastAPI and exposed via `/predict` for real-time inference and `/train` for on-demand retraining.

---

## 📈 Model Performance

Metrics from the most recent training run — tracked live on **[DagsHub/MLflow](https://dagshub.com/sgsatpute/phishing-url-detection-mlops.mlflow)**:

<div align="center">

| Metric | Train | Test |
| :---: | :---: | :---: |
| **F1 Score** | 0.991 | 0.975 |
| **Precision** | 0.990 | 0.970 |
| **Recall** | 0.993 | 0.980 |

</div>

The small train/test gap indicates the model generalizes well without significant overfitting.

---

## ☁️ Deployment

The application is containerized with Docker (`python:3.11-slim-bookworm`) and deployed two independent ways, deliberately chosen to demonstrate two different deployment models:

<table>
<tr>
<td width="50%" valign="top">

### 🅰️ AWS — Manual, Full-Stack Deployment
1. Docker image built locally, pushed to a private **ECR** repo
2. **EC2** (`t3.micro`, free-tier) pulls the image and runs it via Docker
3. Security group opens port `8080` for public access
4. Scoped **IAM** user handles all programmatic access
5. Artifacts sync automatically to **S3** after each run

</td>
<td width="50%" valign="top">

### 🅱️ Render — Automated, GitHub-Integrated
1. Connected directly to this GitHub repository
2. Builds the same `Dockerfile` automatically on every push to `main`
3. Stable, permanent public URL — no manual server management
4. Closer to how a modern CI/CD pipeline deploys in production

</td>
</tr>
</table>

---

## ⚡ Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/sgsatpute/phishing-url-detection-mlops.git
cd phishing-url-detection-mlops

# 2. Install dependencies
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure environment variables (.env in project root)
echo "MONGO_DB_USERNAME=your-mongodb-username" >> .env
echo "MONGO_DB_PASSWORD=your-mongodb-password" >> .env
echo "DAGSHUB_USER_TOKEN=your-dagshub-token" >> .env

# 4. Load data into MongoDB
python push_data.py

# 5. Train the pipeline
python test.py

# 6. Start the API
uvicorn app:app --host 0.0.0.0 --port 8080
```
Interactive docs available at `http://localhost:8080/docs`.

**Or run it with Docker:**
```bash
docker build -t phishing-mlops-repo .
docker run -d -p 8080:8080 --env-file .env --name phishing-app phishing-mlops-repo
```

**Prerequisites:** Python 3.11+ · a MongoDB cluster (free-tier Atlas works) · Docker · a DagsHub account for experiment tracking · AWS credentials (optional, only for S3/EC2)

---

## 📁 Project Structure

```
.
├── images/                       # Architecture and pipeline diagrams
├── network_security/             # Core pipeline source code
│   ├── components/                 # Ingestion, validation, transformation, training
│   ├── pipeline/                    # Orchestration logic
│   ├── entity/                      # Config & artifact dataclasses
│   ├── constant/                    # Shared constants
│   ├── cloud/                       # S3 sync utilities
│   ├── exception/                   # Custom exception handling
│   ├── logging/                     # Logging setup
│   └── utils/                       # Shared helper functions
├── data_schema/schema.yaml       # Schema used for data validation
├── final_model/                  # Latest trained model + preprocessor
├── templates/                    # Jinja2 templates for prediction output
├── valid_data/                   # Sample data for testing /predict
├── app.py                        # FastAPI entry point
├── push_data.py                  # MongoDB data loader
├── test.py                       # Standalone training script
├── Dockerfile                    # Container build configuration
└── requirements.txt              # Python dependencies
```

---

## 🔧 Engineering Challenges Solved

Building and deploying this pipeline surfaced real-world issues that had to be diagnosed and fixed — the kind of debugging that doesn't show up in a tutorial, but does in production:

<details>
<summary><b>Starlette API breaking change</b></summary>
<br>
<code>TemplateResponse</code>'s argument order changed in newer Starlette versions (<code>request</code> moved to the first positional argument), surfacing as a confusing <code>unhashable type: dict</code> error at runtime. Fixed by updating the call signature to match the new API.
</details>

<details>
<summary><b>Silent exception masking</b></summary>
<br>
Two <code>raise NetworkSecurityException</code> calls in the data ingestion component were missing their required arguments entirely, hiding every real error underneath behind a generic <code>TypeError</code>. Fixed to properly propagate the original exception and traceback.
</details>

<details>
<summary><b>MongoDB TLS handshake failures</b></summary>
<br>
Intermittent <code>SSL: TLSV1_ALERT_INTERNAL_ERROR</code> failures during ingestion were traced back to third-party antivirus software performing HTTPS/TLS inspection at the OS level — confirmed by reproducing the identical failure with <code>curl</code> completely outside of Python, ruling out the application code entirely.
</details>

<details>
<summary><b>Debian package repository deprecation</b></summary>
<br>
The original <code>python:3.10-slim-buster</code> Docker base image pointed at an end-of-life Debian release whose package mirrors had been taken offline, causing <code>apt update</code> to fail with 404s. Migrated to <code>python:3.11-slim-bookworm</code>.
</details>

<details>
<summary><b>Python version incompatibility inside the container</b></summary>
<br>
<code>datetime.UTC</code> (used in custom logging) requires Python 3.11+; the original Docker base image used Python 3.10, causing an <code>ImportError</code> that only appeared inside the container, not in local development.
</details>

<details>
<summary><b>Headless OAuth failure in production</b></summary>
<br>
DagsHub's default <code>dagshub.init()</code> call triggers an interactive, browser-based OAuth flow, which hangs indefinitely in a non-interactive server environment like EC2 or Render. Resolved by authenticating via a <code>DAGSHUB_USER_TOKEN</code> environment variable instead.
</details>

<details>
<summary><b>ECR authentication expiry</b></summary>
<br>
Docker's login token for AWS ECR expires periodically, requiring re-authentication (<code>aws ecr get-login-password</code>) before each push or pull — easy to miss when returning to a deployment after a break.
</details>

---

## License

This project is licensed under the MIT License.

<div align="center">

**Built and maintained by [Saurav Satpute](https://github.com/sgsatpute)**

</div>