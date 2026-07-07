# Phishing URL Detection — End-to-End MLOps Pipeline

An automated machine learning system that classifies URLs as **phishing** or **legitimate**. This project covers the complete ML lifecycle — data ingestion from MongoDB, validation with drift detection, transformation, model training with experiment tracking, and a live REST API — fully containerized and deployed to both AWS EC2 and Render.

**🔗 Live demo:** https://phishing-url-detection-mlops.onrender.com/docs

---

## Table of Contents
1. [Overview](#overview)
2. [Live Demo](#live-demo)
3. [Features](#features)
4. [Tech Stack](#tech-stack)
5. [Dataset & Features](#dataset)
6. [Pipeline Architecture](#pipeline)
7. [Model Performance](#performance)
8. [Deployment](#deployment)
9. [Setup & Usage](#setup)
10. [Project Structure](#structure)
11. [Engineering Challenges Solved](#challenges)

---

## <a id="overview"></a>Overview

This project builds a maintainable, production-style pipeline for detecting malicious/phishing websites from their URL characteristics. Rather than a one-off notebook, it's structured as independent, reusable pipeline components — ingestion, validation, transformation, and training — with experiment tracking, schema validation, and statistical drift detection built in throughout.

The trained model is served through a FastAPI application supporting both on-demand retraining (`/train`) and real-time inference (`/predict`), containerized with Docker, and deployed to two separate cloud environments.

---

## <a id="live-demo"></a>Live Demo

| Environment | URL | Notes |
| :--- | :--- | :--- |
| **Render** (primary) | https://phishing-url-detection-mlops.onrender.com/docs | Stable, always-available URL. Free tier spins down after inactivity — first request may take 30–60s to wake up. |
| **AWS EC2** | Manually deployed via Docker on a `t3.micro` instance | Demonstrates a full manual cloud deployment: IAM → S3 → ECR → EC2. |

Try the `/predict` endpoint by uploading `valid_data/test.csv` — it returns an HTML table with a `predicted_column` (`1.0` = legitimate, `0.0` = phishing) for each row.

---

## <a id="features"></a>Features

- **Component-based pipeline** — ingestion, validation, transformation, and training are separated into independent, testable modules
- **Data drift detection** — schema validation plus a Kolmogorov–Smirnov statistical test to catch distribution shifts between train/test splits
- **Experiment tracking** — every training run (hyperparameters, F1/precision/recall) is logged to MLflow via DagsHub
- **Automated artifact sync** — trained models, preprocessors, and validation reports are pushed to AWS S3 after every run
- **REST API** — FastAPI service with `/train` (retrain on demand) and `/predict` (real-time inference) endpoints
- **Dual cloud deployment** — containerized with Docker, deployed manually to AWS EC2 via ECR, and automatically to Render via GitHub integration

---

## <a id="tech-stack"></a>Tech Stack

| Category | Tools |
| :--- | :--- |
| API layer | FastAPI, Uvicorn |
| ML / Data | Scikit-learn, Pandas, NumPy |
| Data store | MongoDB Atlas |
| Experiment tracking | MLflow (via DagsHub) |
| Containerization | Docker |
| Cloud storage | AWS S3 |
| Cloud hosting | AWS EC2, AWS ECR, Render |
| Version control | GitHub |

---

## <a id="dataset"></a>Dataset & Features

The model is trained on **11,055 URL records**, each described by 30 lexical, domain-based, and page-level features that together signal whether a URL is likely to be malicious.

**A few of the key features:**

| Feature | What it captures |
| :--- | :--- |
| `having_IP_Address` | Whether the URL uses a raw IP instead of a domain name |
| `URL_Length` | Overall URL length (longer URLs are more often suspicious) |
| `Shortining_Service` | Whether a URL shortener (e.g. bit.ly) was used |
| `having_At_Symbol` | Presence of "@", which can mask the real destination domain |
| `SSLfinal_State` | Validity/trustworthiness of the SSL certificate |
| `Domain_registeration_length` | How long the domain has been registered |
| `web_traffic` | Site traffic rank as a proxy for legitimacy |
| `age_of_domain` | How long the domain has existed |

---

## <a id="pipeline"></a>Pipeline Architecture

**1. Data Ingestion** — pulls raw records from MongoDB Atlas, splits into train/test sets, stores as artifacts.

**2. Data Validation** — validates incoming data against `data_schema/schema.yaml` (column count, types) and runs a Kolmogorov–Smirnov drift check between train and test distributions.

**3. Data Transformation** — imputes missing values with a `KNNImputer`, applies a preprocessing pipeline, saves outputs as NumPy arrays.

**4. Model Training** — trains multiple candidate models via `GridSearchCV`, logs every run to MLflow (tracked on DagsHub), and persists the best-performing model and preprocessor.

**5. Artifact Sync** — datasets, validation reports, and trained artifacts are synced to an S3 bucket after every pipeline run.

**6. Serving** — the best model is loaded by a FastAPI app and exposed via `/predict` for real-time inference.

---

## <a id="performance"></a>Model Performance

Metrics from the most recent training run (tracked live on [DagsHub/MLflow](https://dagshub.com/sgsatpute/phishing-url-detection-mlops.mlflow)):

| Metric | Train | Test |
| :--- | :--- | :--- |
| F1 Score | 0.991 | 0.975 |
| Precision | 0.990 | 0.970 |
| Recall | 0.993 | 0.980 |

The small train/test gap indicates the model generalizes well without significant overfitting.

---

## <a id="deployment"></a>Deployment

The application is containerized with Docker (`python:3.11-slim-bookworm` base image) and deployed two ways:

**AWS (manual, full-stack cloud deployment):**
1. Docker image built locally and pushed to **AWS ECR**
2. An **EC2** (`t3.micro`, free-tier) instance pulls the image from ECR and runs it via Docker
3. Security group opens port 8080 for public API access
4. Trained artifacts sync to an **S3** bucket after each training run

**Render (automated, GitHub-integrated):**
1. Connected directly to this GitHub repository
2. Builds the same `Dockerfile` automatically on every push to `main`
3. Provides a stable, permanent public URL without manual server management

---

## <a id="setup"></a>Setup & Usage

### Prerequisites
- Python 3.11+
- A MongoDB cluster (e.g. free-tier Atlas)
- Docker (for containerized runs)
- AWS credentials (only needed for S3 artifact sync / EC2 deployment)

### 1. Clone the repository
```bash
git clone https://github.com/sgsatpute/phishing-url-detection-mlops.git
cd phishing-url-detection-mlops
```

### 2. Install dependencies
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables
Create a `.env` file in the project root:
```env
MONGO_DB_USERNAME=your-mongodb-username
MONGO_DB_PASSWORD=your-mongodb-password
DAGSHUB_USER_TOKEN=your-dagshub-token
```

### 4. Load data into MongoDB
```bash
python push_data.py
```

### 5. Run it

**Train the pipeline:**
```bash
python test.py
```

**Start the API:**
```bash
uvicorn app:app --host 0.0.0.0 --port 8080
```
Interactive docs at `http://localhost:8080/docs`.

### 6. Run with Docker
```bash
docker build -t phishing-mlops-repo .
docker run -d -p 8080:8080 --env-file .env --name phishing-app phishing-mlops-repo
```

---

## <a id="structure"></a>Project Structure

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
├── app.py                        # FastAPI entry point
├── push_data.py                  # MongoDB data loader
├── test.py                       # Standalone training script
├── Dockerfile                    # Container build configuration
└── requirements.txt              # Python dependencies
```

---

## <a id="challenges"></a>Engineering Challenges Solved

Building and deploying this pipeline surfaced several real-world issues that had to be diagnosed and fixed:

- **Starlette API breaking change** — `TemplateResponse`'s argument order changed in newer versions, causing an `unhashable type: dict` error at runtime; fixed by updating the call signature.
- **Silent exception masking** — two `raise NetworkSecurityException` calls were missing required arguments, hiding the real underlying errors during debugging; fixed to properly propagate exception details.
- **MongoDB TLS handshake failures** — intermittent `SSL: TLSV1_ALERT_INTERNAL_ERROR` failures traced back to third-party antivirus software performing HTTPS inspection and interfering with TLS negotiation at the OS level (confirmed via `curl` failing identically outside of Python).
- **Debian package repository deprecation** — the original `python:3.10-slim-buster` base image referenced an end-of-life Debian release with dead package mirrors; migrated to `python:3.11-slim-bookworm`.
- **Python version incompatibility** — `datetime.UTC` (used in custom logging) requires Python 3.11+; the original Docker base image used 3.10, causing an `ImportError` only inside the container.
- **Headless OAuth failure** — DagsHub's default `dagshub.init()` triggers an interactive browser-based OAuth flow, which fails in a non-interactive server environment; resolved by authenticating via a `DAGSHUB_USER_TOKEN` environment variable instead.
- **ECR authentication expiry** — Docker's login token for AWS ECR expires periodically, requiring re-authentication (`aws ecr get-login-password`) before pushing or pulling images.

---

## Author

Built and maintained by **Saurav Satpute** — [GitHub](https://github.com/sgsatpute)