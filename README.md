# Phishing URL Detection — End-to-End MLOps Pipeline

An automated machine learning system that classifies URLs as **phishing** or **legitimate**. This project covers the complete ML lifecycle — data ingestion from MongoDB, validation with statistical drift detection, transformation, model training with experiment tracking, and a live REST API — fully containerized and deployed to both AWS EC2 and Render.

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

The trained model is served through a FastAPI application supporting both on-demand retraining (`/train`) and real-time inference (`/predict`), containerized with Docker, and deployed to two separate cloud environments — one set up manually through the full AWS stack (IAM, S3, ECR, EC2), and one through Render's automated GitHub-integrated deployment.

**Overall Architecture**

![Project Architecture](images/architecture.jpg)

---

## <a id="live-demo"></a>Live Demo

| Environment | URL | Notes |
| :--- | :--- | :--- |
| **Render** (primary) | https://phishing-url-detection-mlops.onrender.com/docs | Stable, always-available URL. Free tier spins down after inactivity — first request may take 30–60s to wake up. |
| **AWS EC2** | Deployed manually via Docker on a `t3.micro` instance | Demonstrates a full manual cloud deployment: IAM → S3 → ECR → EC2 → Docker. |

Try the `/predict` endpoint directly by uploading `valid_data/test.csv` — it returns an HTML table with a `predicted_column` for each row (`1.0` = legitimate, `0.0` = phishing).

---

## <a id="features"></a>Features

- **Component-based pipeline** — ingestion, validation, transformation, and training are separated into independent, testable modules that plug into a single orchestrated pipeline.
- **Data drift detection** — schema validation plus a Kolmogorov–Smirnov statistical test to catch distribution shifts between train/test splits, catching silent data quality issues before they reach the model.
- **Experiment tracking** — every training run (hyperparameters, F1/precision/recall) is logged to MLflow via DagsHub, giving a full history of experiments rather than just the final model.
- **Automated artifact sync** — trained models, preprocessors, and validation reports are pushed to AWS S3 after every run, decoupling artifact storage from the compute that produced them.
- **REST API** — FastAPI service with `/train` (retrain on demand) and `/predict` (real-time inference) endpoints, plus interactive Swagger docs out of the box.
- **Dual cloud deployment** — containerized with Docker, deployed manually to AWS EC2 via ECR (full infrastructure ownership), and automatically to Render via GitHub integration (CI/CD-style, redeploys on every push).

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

![URL Features](images/url_features.jpg)

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
| `Google_Index` | Whether the page is indexed by Google (legitimate sites usually are) |

---

## <a id="pipeline"></a>Pipeline Architecture

![Pipeline Workflow Overview](images/pipeline_workflow_diagram.png)

### 1. Data Ingestion
Pulls raw records from MongoDB Atlas, splits them into train/test sets, and stores the result as versioned artifacts for the next stage.

![Data Ingestion Flow](images/data_ingestion_flow.png)

### 2. Data Validation
Validates incoming data against `data_schema/schema.yaml` (column count, data types) and runs a Kolmogorov–Smirnov test to detect statistical drift between the train and test distributions — catching cases where new data no longer resembles what the model was trained on.

![Data Validation Flow](images/data_validation_flow.png)

### 3. Data Transformation
Missing values are imputed using a `KNNImputer`, features are passed through a preprocessing pipeline, and the resulting arrays are saved as NumPy files ready for efficient model training.

![Data Transformation Flow](images/data_transformation_flow.png)

### 4. Model Training
Multiple candidate classification models are trained using `GridSearchCV` for hyperparameter tuning. Every run — parameters, F1, precision, recall — is logged to MLflow (tracked live on DagsHub), and the best-performing model and preprocessor are persisted.

![Model Training Flow](images/model_training_flow.png)

### 5. Artifact Sync
All pipeline artifacts — datasets, validation reports, trained models, and preprocessors — are automatically synced to an AWS S3 bucket after every run, for persistence and reproducibility independent of any single machine.

### 6. Serving
The best model is loaded by a FastAPI application and exposed through a `/predict` endpoint for real-time inference, and a `/train` endpoint to trigger retraining on demand.

---

## <a id="performance"></a>Model Performance

Metrics from the most recent training run (tracked live on [DagsHub/MLflow](https://dagshub.com/sgsatpute/phishing-url-detection-mlops.mlflow)):

| Metric | Train | Test |
| :--- | :--- | :--- |
| F1 Score | 0.991 | 0.975 |
| Precision | 0.990 | 0.970 |
| Recall | 0.993 | 0.980 |

The small gap between train and test metrics indicates the model generalizes well without significant overfitting.

---

## <a id="deployment"></a>Deployment

The application is containerized with Docker (`python:3.11-slim-bookworm` base image) and deployed in two independent ways, deliberately chosen to demonstrate two different deployment models:

### AWS — manual, full-stack cloud deployment
1. Docker image built locally and pushed to a private **AWS ECR** repository
2. An **EC2** (`t3.micro`, free-tier eligible) instance pulls the image from ECR and runs it via Docker
3. A security group opens port 8080 so the API is publicly reachable
4. An **IAM** user with scoped permissions (S3, ECR, EC2 only) handles all programmatic access
5. Trained artifacts sync automatically to an **S3** bucket after each training run

### Render — automated, GitHub-integrated deployment
1. Connected directly to this GitHub repository
2. Builds the same `Dockerfile` automatically on every push to `main`
3. Provides a stable, permanent public URL without any manual server management — closer to how a modern CI/CD pipeline would deploy this in production

---

## <a id="setup"></a>Setup & Usage

### Prerequisites
- Python 3.11+
- A MongoDB cluster (e.g. free-tier Atlas)
- Docker (for containerized runs)
- AWS credentials (only needed for S3 artifact sync / EC2 deployment)
- A DagsHub account (for MLflow experiment tracking)

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
Interactive docs available at `http://localhost:8080/docs`.

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
├── valid_data/                   # Sample data for testing /predict
├── app.py                        # FastAPI entry point
├── push_data.py                  # MongoDB data loader
├── test.py                       # Standalone training script
├── Dockerfile                    # Container build configuration
└── requirements.txt              # Python dependencies
```

---

## <a id="challenges"></a>Engineering Challenges Solved

Building and deploying this pipeline surfaced a number of real-world issues that had to be diagnosed and fixed — the kind of debugging work that doesn't show up in a tutorial, but does in production:

- **Starlette API breaking change** — `TemplateResponse`'s argument order changed in newer Starlette versions (`request` moved to the first positional argument), which surfaced as a confusing `unhashable type: dict` error at runtime. Fixed by updating the call signature to match the new API.
- **Silent exception masking** — two `raise NetworkSecurityException` calls in the data ingestion component were missing their required arguments entirely, which meant every real error underneath them was hidden behind a generic `TypeError`. Fixed to properly propagate the original exception and traceback.
- **MongoDB TLS handshake failures** — intermittent `SSL: TLSV1_ALERT_INTERNAL_ERROR` failures during data ingestion were eventually traced back to third-party antivirus software performing HTTPS/TLS inspection at the OS level — confirmed by reproducing the identical failure with `curl` completely outside of Python, ruling out the application code.
- **Debian package repository deprecation** — the original `python:3.10-slim-buster` Docker base image pointed at an end-of-life Debian release whose package mirrors had been taken offline, causing `apt update` to fail with 404s. Migrated to `python:3.11-slim-bookworm`.
- **Python version incompatibility inside the container** — `datetime.UTC` (used in custom logging) requires Python 3.11+; the original Docker base image used Python 3.10, causing an `ImportError` that only appeared inside the container, not in local development.
- **Headless OAuth failure in production** — DagsHub's default `dagshub.init()` call triggers an interactive, browser-based OAuth flow, which hangs indefinitely in a non-interactive server environment like EC2 or Render. Resolved by authenticating via a `DAGSHUB_USER_TOKEN` environment variable instead.
- **ECR authentication expiry** — Docker's login token for AWS ECR expires periodically, requiring re-authentication (`aws ecr get-login-password`) before each push or pull — easy to miss when returning to a deployment after a break.

---

## Author

Built and maintained by **Saurav Satpute** — [GitHub](https://github.com/sgsatpute)