# SealMusic — AI Music Platform

An artificial intelligence platform that lets people create songs with no musical background, combining music generation with social features. Starting from **a PDF** (topic context) and **a reference song** (style), the system generates an original song ready to publish on the platform.

## Full Documentation

[Open full report ➤ ](readme_rss/readme.pdf)    <-

---

## Backend

The backend is built in **Python on AWS** and is organized into two functional modules:

1. **Authentication and User Service** (Cognito + RDS)
2. **AI Song Generation Pipeline** (S3 + generative AI + audio processing)

Amazon S3 acts as intermediate storage between each stage of the pipeline, and Amazon RDS (PostgreSQL) serves as the transactional database (OLTP).

### AWS AI Services Used

| AWS Service | Role in the backend | Where it's used |
|---|---|---|
| **AWS Bedrock** (Converse API) | Generative LLM that writes the song lyrics | `llamar_qwen()` — generates the educational lyrics following the meter of the reference song, using **only** concepts extracted from the PDF |
| **Amazon Cognito** | Identity, authentication, and token (JWT) issuance | `registrar_usuario()`, `iniciar_sesion()` — sign up, confirmation, login, and user verification |
| **Amazon EC2 (Batch Processing)** | Parallel compute for segmented song generation and heavy audio processing (Demucs/Whisper/TTS) | Separation, transcription, and synthesis stages of the pipeline |
| **Amazon S3** | Storage for PDFs, original/processed audio, and final results | `subir_archivos()`, `genera_url()`, and as the bridge between each pipeline function |
| **Amazon SageMaker** *(analytics layer)* | Training/inference for classification models (music genre, topic, churn/fraud detection) | Complements the generative pipeline with AI over the DWH (see DSS section) |
| **Amazon Redshift ML** *(analytics layer)* | SQL-based predictions over the Data Warehouse (e.g., Premium propensity, API consumption anomalies) | Not part of the real-time pipeline, but consumes its historical output |

> **AWS Bedrock** is the heart of the product's generative AI: it turns the plain text of an academic PDF into song lyrics that follow the rhythmic structure of a reference song, without straying from the source content (hallucination mitigation via a restrictive prompt).

### Song Generation Pipeline

Full end-to-end flow:

```
User uploads PDF + reference song
        │
        ▼
1. subir_archivos()              → Uploads PDF and song to S3
2. extraer_texto_pdf_s3()        → Extracts text from the PDF (pdfplumber)
3. separar_y_subir_audio()       → Separates vocals/instrumental (Demucs) and uploads to S3
4. transcribir_audio_s3()        → Transcribes the vocals with timestamps (Whisper)
5. llamar_qwen()                 → AWS Bedrock generates the educational lyrics
6. generar_y_mezclar_tts_s3()    → Clones the voice (XTTS v2) and mixes it over the instrumental
7. genera_url()                  → Presigned S3 URL (1h) with the result
8. agregar_registro_csv_s3()     → Logs the song in the control CSV
```

#### Core Functions

| Function | Purpose | Technology |
|---|---|---|
| `extraer_texto_pdf_s3(bucket, key)` | Downloads a PDF from S3 and concatenates the text of all its pages | pdfplumber, boto3 (S3) |
| `separar_y_subir_audio(archivo, bucket, prefix)` | Separates the reference song into vocal and instrumental tracks and uploads the resulting MP3s to S3 | Demucs (`--two-stems=vocals`), ffmpeg |
| `transcribir_audio_s3(bucket, key, model, lang)` | Downloads an audio file from S3 and transcribes it, returning full text plus timestamped segments | OpenAI Whisper |
| `llamar_qwen(texto_pdf, letra_original, num_lines, idioma)` | Generates the educational lyrics from the PDF, preserving the original meter | **AWS Bedrock (Converse API)** |
| `generar_y_mezclar_tts_s3(...)` | Synthesizes each line with the cloned reference voice and overlays it onto the instrumental at Whisper's timestamps | Coqui TTS (XTTS v2), pydub |
| `subir_archivos(path1, path2)` | Uploads the original PDF and reference song to S3 | boto3 (S3) |
| `genera_url(bucket, key)` | Generates a presigned S3 URL (1h) to deliver the result | boto3 (S3, SigV4) |
| `agregar_registro_csv_s3(bucket, csv_key, registro)` | Appends a control row (song path, lyrics path, cognito_id) to a CSV in S3 | boto3 (S3), `csv` module |

### Authentication and User Service (Cognito + RDS)

Orchestrates the full registration and login cycle, syncing **Amazon Cognito** (identity) with **Amazon RDS PostgreSQL** (transactional profile):

| Step | Action | AWS Service |
|---|---|---|
| 1 | `sign_up()` with email, password, username, birthdate, country, state | Amazon Cognito |
| 2 | `admin_confirm_sign_up()` confirms the account automatically | Amazon Cognito |
| 3 | `admin_update_user_attributes()` sets `email_verified = true` | Amazon Cognito |
| 4 | `INSERT` into the `usuarios` table with the synced `UserSub` (cognito_id) | Amazon RDS (PostgreSQL) |

| Function | Purpose |
|---|---|
| `get_secret_hash(username)` | Computes the HMAC-SHA256 required by Cognito for clients with a configured secret |
| `registrar_usuario(...)` | Orchestrates the full sign-up: Cognito `sign_up` + confirmation + verification + `INSERT` into RDS |
| `iniciar_sesion(email, password)` | Authenticates against Cognito (`USER_PASSWORD_AUTH`) and retrieves the `cognito_id` |

**Error handling:**
- `UsernameExistsException` → HTTP 400, email already registered.
- `InvalidPasswordException` → HTTP 400, Cognito password policy not met.
- `NotAuthorizedException` / `UserNotFoundException` on login → HTTP 401 with a generic message (prevents user enumeration).

### Backend Technology Stack

| Category | Library / Service | Use |
|---|---|---|
| Storage | boto3 (S3) | Download/upload of PDFs, audio, and results; presigned URLs |
| Identity | boto3 (Cognito) | User registration, confirmation, and authentication |
| Database | psycopg2 | Direct insertion of the user profile into PostgreSQL (RDS) |
| Text extraction | pdfplumber | Plain-text extraction per page from the context PDF |
| Audio separation | Demucs + ffmpeg | Vocal/instrumental separation and WAV → MP3 conversion |
| Transcription | OpenAI Whisper | Transcription with timestamped segments |
| **Lyrics generation (AI)** | **AWS Bedrock (Converse API)** | LLM that writes the educational lyrics from the PDF |
| Voice synthesis | Coqui TTS (XTTS v2) | Multilingual voice cloning, line by line |
| Audio mixing | pydub | Overlaying generated lines onto the instrumental |
| API / Web | FastAPI | HTTP exception handling for the authentication service |

### Code Security

- PostgreSQL queries use **prepared parameters** (`cur.execute` with `%s` placeholders), preventing SQL injection.
- Login error messages are **generic**, avoiding disclosure of whether an email exists.
- **Risk identified:** the Cognito `CLIENT_SECRET` and RDS credentials (`DB_USER`, `DB_PASS`) are hardcoded directly in the source code. It is recommended to move them to **AWS Secrets Manager** or environment variables injected by the runtime environment (Lambda/EC2).
- Temporary files (PDFs, audio) are processed inside `tempfile.TemporaryDirectory()`, which is automatically deleted once each function completes.

---

## Data Architecture

SealMusic follows a **Data-in-Motion** paradigm under a **Microservices with Database-per-Service** model, separating reads from writes (CQRS):

```
Create Song      → OLTP (create song)      → ETL → Song DB
Create Account   → OLTP (create account)   → ETL → Users DB
Interact         → OLTP (interaction)      → ETL → Interactions DB
                                                        │
                                                        ▼
                              Song/Users DB (Staging) → Final ETL → OLAP Cube → Graph DB (Recommendations)
```

### Core Components

| Component | Database | Type | Purpose |
|---|---|---|---|
| Create Song | Song DB (RDS) | OLTP | Metadata and audio files |
| Create Account | Users DB (RDS) | OLTP | User identity and profile |
| Interact | Interactions DB (RDS) | OLTP | Real-time telemetry |
| Analysis | Final Data Cube | OLAP | Analytical Data Warehouse (Redshift) |
| Recommendations | Graph DB | Graph | Recommendation engine |

### Notable ETL Techniques

- **Fuzzy Matching (RapidFuzz)**: normalizes spelling variations of country/state (e.g., "Mejico", "mexica" → Mexico).
- **TF-IDF + Logistic Regression/SVM**: classifies the music genre from the generated lyrics.
- **Gumbel Copula**: models nonlinear dependencies between AI model quality, user retention, and infrastructure cost in DSS simulations.

### ETL Performance to the OLAP Cube

| Data Volume | Time on AWS | Observation |
|---|---|---|
| 500,000 records | 12 sec | Optimal for testing |
| 12,000,000 records | 6 min 40 sec | AWS optimizes with columnar storage |
| 200,000,000 records | 2 hours | Overnight batch recommended |

---

## Platform Security and Scalability

| Layer | AWS Service | Protection |
|---|---|---|
| Identity and authentication | Amazon Cognito | MFA, OAuth2, signed JWT tokens |
| Encryption in transit | TLS 1.3 | All API and DB connections encrypted |
| Encryption at rest | AWS KMS | Encrypted S3 buckets and RDS databases |
| Access control | IAM Roles | Least-privilege principle per service |
| DDoS protection | AWS Shield + WAF | Automatic blocking of volumetric attacks |
| Monitoring and auditing | AWS CloudTrail | Immutable log of all operations |

- **OLAP Cube (Redshift):** supports 500+ million records with distributed columnar storage.
- **Read replicas:** absorb frontend and ETL traffic without impacting the primary RDS instance.

---

## Summary

| Component | Problem it Solves | Measurable Impact |
|---|---|---|
| Microservices + OLTP | Isolated failure per domain | 99.9% availability per service |
| **AWS Bedrock (LLM)** | Lyrics generation without musical knowledge from the user | Educational lyrics faithful to the source PDF |
| ETL with Fuzzy Matching | Dirty location data | Automatic standardization of 190+ countries |
| TF-IDF + SVM Classifier | Unlabeled song metadata | Automatic genre/topic classification |
| OLAP Cube (Redshift) | Slow reporting over transactional data | From 56 min to 6:40 min for 12M records |
| Graph DB | Generic recommendations | Real-time personalization |
| SageMaker + Redshift ML | AI confined to isolated notebooks | ML directly in SQL over 500M+ records |

---

*SealMusic —· LuisMData*
