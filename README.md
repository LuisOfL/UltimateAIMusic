# SealMusic — AI Music Platform

Plataforma de inteligencia artificial que permite crear canciones sin conocimientos musicales, combinando generación musical con funciones de red social. A partir de **un PDF** (contexto temático) y **una canción de referencia** (estilo), el sistema genera una canción original publicable en la plataforma.

## Documentación completa

📄 [Abrir reporte completo](readme_rss/readme.pdf)



---

## 🧠 Backend

El backend está construido en **Python sobre AWS** y se organiza en dos módulos funcionales:

1. **Servicio de Autenticación y Usuarios** (Cognito + RDS)
2. **Pipeline de Generación de Canciones por IA** (S3 + IA generativa + procesamiento de audio)

Amazon S3 actúa como almacenamiento intermedio entre cada etapa del pipeline, y Amazon RDS (PostgreSQL) como base de datos transaccional (OLTP).

### Servicios de AWS de IA utilizados

| Servicio AWS | Rol en el backend | Dónde se usa |
|---|---|---|
| **AWS Bedrock** (Converse API) | LLM generativo que redacta la letra de la canción | `llamar_qwen()` — genera la letra educativa siguiendo la métrica de la canción de referencia, usando **solo** conceptos extraídos del PDF |
| **Amazon Cognito** | Identidad, autenticación y emisión de tokens (JWT) | `registrar_usuario()`, `iniciar_sesion()` — sign up, confirmación, login y verificación de usuarios |
| **Amazon EC2 (Batch Processing)** | Cómputo paralelo para generación de canciones por segmentos y procesamiento de audio pesado (Demucs/Whisper/TTS) | Etapas de separación, transcripción y síntesis del pipeline |
| **Amazon S3** | Almacenamiento de PDFs, audios originales/procesados y resultados finales | `subir_archivos()`, `genera_url()` y como puente entre cada función del pipeline |
| **Amazon SageMaker** *(capa analítica)* | Entrenamiento/inferencia de modelos de clasificación (género musical, tema, detección de churn/fraude) | Complementa al pipeline generativo con IA sobre el DWH (ver sección DSS) |
| **Amazon Redshift ML** *(capa analítica)* | Predicciones vía SQL sobre el Data Warehouse (ej. propensión a Premium, anomalías de consumo de API) | No forma parte del pipeline en tiempo real, pero consume su output histórico |

> El uso de **AWS Bedrock** es el corazón de la IA generativa del producto: convierte el texto plano de un PDF académico en una letra de canción coherente con la estructura rítmica de una canción de referencia, sin salirse del contenido fuente (mitigación de alucinaciones vía prompt restrictivo).

### Pipeline de Generación de Canciones

Flujo completo, de principio a fin:

```
Usuario sube PDF + canción de referencia
        │
        ▼
1. subir_archivos()              → Sube PDF y canción a S3
2. extraer_texto_pdf_s3()        → Extrae texto del PDF (pdfplumber)
3. separar_y_subir_audio()       → Separa voz/instrumental (Demucs) y sube a S3
4. transcribir_audio_s3()        → Transcribe la voz con timestamps (Whisper)
5. llamar_qwen()                 → 🧠 AWS Bedrock genera la letra educativa
6. generar_y_mezclar_tts_s3()    → Clona la voz (XTTS v2) y mezcla sobre el instrumental
7. genera_url()                  → URL prefirmada de S3 (1h) con el resultado
8. agregar_registro_csv_s3()     → Registra la canción en el CSV de control
```

#### Funciones principales

| Función | Propósito | Tecnología |
|---|---|---|
| `extraer_texto_pdf_s3(bucket, key)` | Descarga un PDF de S3 y concatena el texto de todas sus páginas | pdfplumber, boto3 (S3) |
| `separar_y_subir_audio(archivo, bucket, prefix)` | Separa la canción de referencia en voz e instrumental y sube los MP3 a S3 | Demucs (`--two-stems=vocals`), ffmpeg |
| `transcribir_audio_s3(bucket, key, model, lang)` | Transcribe el audio y devuelve texto + segmentos con marcas de tiempo | OpenAI Whisper |
| `llamar_qwen(texto_pdf, letra_original, num_lines, idioma)` | Genera la letra educativa a partir del PDF, respetando la métrica original | **AWS Bedrock (Converse API)** |
| `generar_y_mezclar_tts_s3(...)` | Sintetiza cada línea con la voz de referencia clonada y la mezcla sobre el instrumental | Coqui TTS (XTTS v2), pydub |
| `subir_archivos(path1, path2)` | Sube PDF y canción de referencia originales a S3 | boto3 (S3) |
| `genera_url(bucket, key)` | Genera una URL prefirmada de S3 (1h) para entregar el resultado | boto3 (S3, SigV4) |
| `agregar_registro_csv_s3(bucket, csv_key, registro)` | Agrega una fila de control (ruta canción, letra, cognito_id) a un CSV en S3 | boto3 (S3), módulo `csv` |

### Servicio de Autenticación y Usuarios (Cognito + RDS)

Orquesta el ciclo completo de registro y login, sincronizando **Amazon Cognito** (identidad) con **Amazon RDS PostgreSQL** (perfil transaccional):

| Paso | Acción | Servicio AWS |
|---|---|---|
| 1 | `sign_up()` con email, password, username, birthdate, country, state | Amazon Cognito |
| 2 | `admin_confirm_sign_up()` confirma la cuenta automáticamente | Amazon Cognito |
| 3 | `admin_update_user_attributes()` marca `email_verified = true` | Amazon Cognito |
| 4 | `INSERT` en la tabla `usuarios` con el `UserSub` (cognito_id) sincronizado | Amazon RDS (PostgreSQL) |

| Función | Propósito |
|---|---|
| `get_secret_hash(username)` | Calcula el HMAC-SHA256 exigido por Cognito para clientes con secret configurado |
| `registrar_usuario(...)` | Orquesta el alta completa: Cognito `sign_up` + confirmación + verificación + `INSERT` en RDS |
| `iniciar_sesion(email, password)` | Autentica contra Cognito (`USER_PASSWORD_AUTH`) y recupera el `cognito_id` |

**Manejo de errores:**
- `UsernameExistsException` → HTTP 400, correo ya registrado.
- `InvalidPasswordException` → HTTP 400, política de contraseña no cumplida.
- `NotAuthorizedException` / `UserNotFoundException` en login → HTTP 401 con mensaje genérico (evita enumeración de usuarios).

### Stack tecnológico del backend

| Categoría | Librería / Servicio | Uso |
|---|---|---|
| Almacenamiento | boto3 (S3) | Descarga/subida de PDFs, audios y resultados; URLs prefirmadas |
| Identidad | boto3 (Cognito) | Registro, confirmación y autenticación de usuarios |
| Base de datos | psycopg2 | Inserción directa del perfil de usuario en PostgreSQL (RDS) |
| Extracción de texto | pdfplumber | Lectura de texto plano por página del PDF de contexto |
| Separación de audio | Demucs + ffmpeg | Separación de voz/instrumental y conversión WAV → MP3 |
| Transcripción | OpenAI Whisper | Transcripción con segmentos y timestamps |
| **Generación de letra (IA)** | **AWS Bedrock (Converse API)** | LLM que redacta la letra educativa a partir del PDF |
| Síntesis de voz | Coqui TTS (XTTS v2) | Clonación de voz multilingüe línea por línea |
| Mezcla de audio | pydub | Overlay de las líneas generadas sobre el instrumental |
| API / Web | FastAPI | Manejo de excepciones HTTP del servicio de autenticación |

### Seguridad del código

- Las consultas a PostgreSQL usan **parámetros preparados** (`cur.execute` con placeholders `%s`), previniendo inyección SQL.
- Los mensajes de error de login son **genéricos**, evitando revelar si el correo existe.
- ⚠️ **Riesgo detectado:** `CLIENT_SECRET` de Cognito y las credenciales de RDS (`DB_USER`, `DB_PASS`) están escritos directamente en el código. Se recomienda moverlos a **AWS Secrets Manager** o variables de entorno inyectadas por el entorno de ejecución (Lambda/EC2).
- Los archivos temporales (PDFs, audios) se procesan dentro de `tempfile.TemporaryDirectory()`, que se elimina automáticamente al finalizar cada función.

---

## 🏗️ Arquitectura de Datos

SealMusic sigue un paradigma de **Datos en Movimiento** bajo un modelo de **Microservicios con Base de Datos por Servicio** (Database-per-Service), separando lectura de escritura (CQRS):

```
Crear Canción    → OLTP (crear canción)   → ETL → BD Canción
Crear Cuenta     → OLTP (crear cuenta)    → ETL → BD Usuarios
Interactuar      → OLTP (interacción)     → ETL → BD Interacciones
                                                        │
                                                        ▼
                              BD Canción/Usuarios (Staging) → ETL Final → Cubo OLAP → BD Grafos (Recomendaciones)
```

### Componentes principales

| Componente | Base de Datos | Tipo | Propósito |
|---|---|---|---|
| Crear Canción | BD Canción (RDS) | OLTP | Metadatos y archivos de audio |
| Crear Cuenta | BD Usuarios (RDS) | OLTP | Identidad y perfil de usuario |
| Interactuar | BD Interacciones (RDS) | OLTP | Telemetría en tiempo real |
| Análisis | Cubo de Datos Final | OLAP | Data Warehouse analítico (Redshift) |
| Recomendaciones | BD Grafo | Grafo | Motor de recomendaciones |

### ETL destacado

- **Fuzzy Matching (RapidFuzz)**: normaliza variaciones ortográficas de país/estado (ej. "Mejico", "mexica" → México).
- **TF-IDF + Logistic Regression/SVM**: clasifica el género musical a partir de la letra generada.
- **Cópula de Gumbel**: modela dependencias no lineales entre calidad del modelo IA, retención de usuarios y costo de infraestructura en simulaciones DSS.

### Rendimiento del ETL hacia el Cubo OLAP

| Volumen de datos | Tiempo en AWS | Observación |
|---|---|---|
| 500,000 registros | 12 seg | Óptimo para pruebas |
| 12,000,000 registros | 6 min 40 seg | AWS optimiza con columnar storage |
| 200,000,000 registros | 2 horas | Batch nocturno recomendado |

---

## 🔒 Seguridad y Escalabilidad de la Plataforma

| Capa | Servicio AWS | Protección |
|---|---|---|
| Identidad y autenticación | Amazon Cognito | MFA, OAuth2, tokens JWT firmados |
| Cifrado en tránsito | TLS 1.3 | Todas las conexiones API y BD cifradas |
| Cifrado en reposo | AWS KMS | Buckets S3 y bases de datos RDS cifradas |
| Control de acceso | IAM Roles | Principio de mínimo privilegio por servicio |
| Protección DDoS | AWS Shield + WAF | Bloqueo automático de ataques volumétricos |
| Monitoreo y auditoría | AWS CloudTrail | Log inmutable de todas las operaciones |

- **Cubo OLAP (Redshift):** soporta +500 millones de registros con almacenamiento columnar distribuido.
- **Réplicas de lectura:** absorben tráfico del frontend y del ETL sin afectar al RDS primario.

---

## 📌 Resumen

| Componente | Problema que resuelve | Impacto medible |
|---|---|---|
| Microservicios + OLTP | Fallo aislado por dominio | 99.9% disponibilidad por servicio |
| **AWS Bedrock (LLM)** | Generación de letras sin conocimiento musical del usuario | Letra educativa fiel al PDF fuente |
| ETL con Fuzzy Matching | Datos sucios de ubicación | Estandarización automática de 190+ países |
| Clasificador TF-IDF + SVM | Metadatos de canciones sin etiquetar | Clasificación automática de género/tema |
| Cubo OLAP (Redshift) | Reportes lentos sobre transaccional | De 56 min → 6:40 min para 12M registros |
| BD de Grafos | Recomendaciones genéricas | Personalización en tiempo real |
| SageMaker + Redshift ML | IA solo en notebooks aislados | ML directamente en SQL sobre 500M+ datos |

---

*SealMusic — Propuesta Expoescom · LuisMData*
