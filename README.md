# Final Music

**Final Music** es una plataforma innovadora impulsada por Inteligencia Artificial diseñada para transformar contenido estático (texto e imágenes) y referencias musicales en nuevas composiciones melódicas personalizadas.

##  Funcionalidades Principales

* **Creación basada en referencias:** Genera nuevas canciones a partir de una canción base enviada por el usuario [cite: 3].
* **Melodías Educativas:** Sube un archivo PDF, elige un estilo musical y la IA creará una melodía que resuma el contenido del documento [cite: 4].
* **Imagen a Música:** Sube una imagen y la plataforma creará una melodía inspirada en los elementos visuales de la misma [cite: 5, 41].

##  Stack Tecnológico

El proyecto utiliza tecnologías de vanguardia para garantizar escalabilidad y rendimiento:
* **Cloud:** AWS (Amazon Web Services) [cite: 6, 45].
* **Backend:** Python, FastAPI, PySpark [cite: 6].
* **Frontend:** Flet [cite: 6].
* **Procesamiento de Texto:** Amazon Textract para la extracción de contenido en PDFs [cite: 78].

##  Arquitectura y Flujo de Trabajo

1.  **Petición del Usuario:** El usuario inicia una solicitud a través de la interfaz [cite: 7, 8].
2.  **Análisis de Datos:** Se extraen y guardan las *features* en una base de datos para su análisis posterior [cite: 9].
3.  **Procesamiento ML:** Se realiza la petición al modelo de Machine Learning correspondiente [cite: 10].
4.  **Generación de Contenido:**
    * Se extrae el texto del PDF (vía Amazon Textract) [cite: 62, 67, 78].
    * Se analiza el estilo y se extrae la letra de una canción de referencia [cite: 53, 66].
    * Un **LLM** procesa la información para crear una nueva letra sincronizada [cite: 55, 70].
    * Un **ML Engine** procesa la letra junto con una pista de fondo para generar el resultado final [cite: 73, 76, 77].

##  Alcance del MVP (Producto Mínimo Viable)

* **Funcionalidad prioritaria:** Finalización de la creación de canciones basadas en PDF [cite: 44].
* **Interfaz:** UI completa con pantallas de inicio, login y configuración listas [cite: 11, 45].
* **Limitaciones del modelo:**
    * El PDF se utiliza únicamente para contenido teórico (texto) [cite: 47].
    * No se procesan fórmulas matemáticas ni imágenes dentro de los archivos PDF [cite: 47].
    * La letra generada se sincroniza para asegurar una melodía agradable al oído [cite: 48].

##  Interfaz de Usuario

La aplicación cuenta con una navegación intuitiva que incluye:
* **Splash Screen:** Pantalla de carga inicial [cite: 11].
* **Inicio:** Descripción breve de la aplicación y botón de inicio [cite: 16, 18, 19].
* **Main:** Panel principal para gestionar y crear nuevas piezas musicales [cite: 12, 22].
* **Configuración:** Ajustes personalizados para el usuario [cite: 15, 39].

---
*Documentación generada en base al proyecto "Final Music".*
