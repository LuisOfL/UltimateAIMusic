# SealMusic

SealMusic es una futura startup de inteligencia artificial que permite crear canciones sin necesidad de tener conocimientos musicales. La plataforma combina generación musical con funciones de red social para compartir y descubrir contenido. Una de sus principales características es la creación de canciones a partir de dos entradas: un documento PDF que proporciona el contexto y una canción de referencia que define el estilo musical.

Utiliza modelos de Inteligencia artificial para crear las melodías, tiene diferentes opciones la función principal utiliza principalmente AWS Boto3 (SDK de Amazon Web Services) para interactuar con servicios en la nube como Amazon S3 y AWS Bedrock. S3 se usa como almacenamiento central para archivos PDF, audios, canciones e información procesada, mientras que Bedrock permite ejecutar modelos de lenguaje como Gemma para generar texto a partir de instrucciones estructuradas. Además, se generan URLs presignadas para acceso seguro a los archivos almacenados esta opción funciona con computo distribuido para reducir su latencia.

Aca va una imagen

---

## Resumen de alojamiento

Este sistema cuenta con 3 OLTP para extracción de datos

• OLTP de Creación de Canciones: Gestiona la generación de contenido musical, registrando los metadatos de las piezas creadas, incluyendo su duración, idioma, tema, género y el identificador del autor. 

### ETL de Usuarios:

• Extracción: Obtiene datos básicos de los usuarios desde la base de datos de registro.  
• Transformación: Realiza limpieza de datos eliminando espacios y verificando valores nulos. Calcula la edad a partir de la fecha de nacimiento y genera un rango de edad, además de estandarizar nombres de países y estados mediante técnicas de fuzzy matching para corregir errores ortográficos. Finalmente, crea columnas adicionales como el tipo de membresía. 

## UsersETL

Esta base de datos es la encargada de la gestión de identidades y perfilamiento geográfico de los usuarios.

• Función: Almacena la información de los usuarios registrados en la plataforma y su ubicación física.  
• Tablas clave:  
  o ubicacion: Contiene el desglose geográfico (continente, país, estado).  
  o usuario: Registra los datos personales, incluyendo nombre, edad, rango de edad, tipo de membresía y fecha de creación, manteniendo una relación de integridad referencial con la tabla de ubicaciones.

---

• OLTP de Creación de Cuentas (Usuarios): Se encarga del registro de usuarios, capturando información como nombre de usuario, correo electrónico, fecha de nacimiento, estado y país de origen, integrándose con Amazon Cognito para la autenticación. 

### ETL de Canciones:

• Extracción: Toma los metadatos de las canciones generadas desde su sistema transaccional.  
• Transformación: Calcula la duración de la pista. Aplica modelos de aprendizaje automático (TF-IDF y clasificadores como Logistic Regression o SVM) para determinar el género musical a partir de la letra. Utiliza modelos como MiniLM para extraer automáticamente el idioma y el tema de la canción desde el texto de la letra.

## CancionETL

Esta base de datos centraliza todo lo relacionado con el contenido musical generado mediante inteligencia artificial.

• Función: Gestionar los metadatos de las piezas musicales que se crean en la plataforma y asegurar la trazabilidad del autor.  
• Tablas clave:  
  o cancion: Almacena características técnicas como duración, idioma, tema y género, además de asociar la canción a su autor mediante un identificador (id_autor).  
• Optimización: Incluye índices específicos para agilizar las búsquedas por autor y por tema musical, lo cual es fundamental para el rendimiento del sistema.

---

• OLTP de Interacciones: Registra la telemetría y el comportamiento del usuario con las canciones, incluyendo métricas como tiempo de reproducción, eventos de "like", "dislike" y descargas, además de capturar el contexto del dispositivo utilizado (sistema operativo, idioma y tipo de conexión).  

### ETL de Interacciones:

• Extracción: Captura datos de telemetría y eventos de usuario en tiempo real.  
• Transformación: La fecha y hora se procesan para generar una surrogate key (llave subrogada) y desglosarla en año, mes, día y hora. Realiza feature engineering convirtiendo los eventos de interacción (like, dislike, descarga) en variables binarias y limpia los datos del contexto del dispositivo antes de cargarlos al sistema

## Interacciones

Esta es la base de datos de telemetría y comportamiento, diseñada para capturar la experiencia del usuario final con el contenido.

• Función: Registrar cómo los usuarios consumen la música y qué dispositivos utilizan.  
• Tablas clave:  
  o fecha: Catálogo temporal que desglosa el momento exacto de la interacción (día, mes, año, hora).  
  o dispositivo: Registra las características técnicas de los dispositivos (tipo, sistema operativo, idioma y tipo de conexión).  
  o interacciones: Es la tabla central que vincula al usuario, la canción, el momento (id_fecha) y el dispositivo. Registra eventos como tipo_evento (play, pause, etc.), tiempo_reproduccion y acciones de feedback del usuario (dio_like, dio_dislike, descargada).

---

## Resumen del Cubo OLAP y DSS

El modelo multidimensional actúa como el "cerebro" analítico de la plataforma: 

• Estructura del Cubo: Se organiza mediante un esquema de estrella donde las tablas de hechos (Hechos_Interacciones, Hechos_Adquisicion, Hechos_Simulaciones, Hechos_Data_Quality) se vinculan a dimensiones clave: dim_cancion, dim_usuario, dim_ubicacion, dim_fecha_hora, dim_dispositivo y dim_escenario.  

• Capacidades del DSS: El componente DSS permite realizar proyecciones de negocio mediante el uso de dim_escenario, facilitando comparativas entre proyecciones base, optimistas y pesimistas sobre el crecimiento de la plataforma.  

• Métricas Estratégicas: El cubo permite calcular indicadores críticos como la Retención (N-Month Retention), Velocidad de Activación, Engagement Ratio, Skip Rate (tasa de rechazo) y la Concentración de Consumo (Regla de Pareto) para identificar la dependencia de artistas o usuarios específicos.  

---

## Justificación de la Arquitectura

La decisión de estructurar el sistema de esta manera responde a necesidades específicas del negocio:

1. Resolución de la "Ceguera de Marketing": Al integrar datos de ubicación y comportamiento en dimensiones, el cubo permite segmentar usuarios de forma precisa, evitando que el presupuesto publicitario se desperdicie en usuarios inactivos.  

2. Mitigación del Churn de Contenido: La estructura permite cruzar datos de canciones (tema, género) con tasas de "skip" del usuario, lo que ayuda a entender si la fuga de usuarios se debe a una desalineación de gustos o a la calidad del contenido generado por IA.  

3. Optimización del "Aha! Moment": La granularidad de los Hechos_Interacciones permite identificar en qué punto exacto del historial de consumo un usuario gratuito desarrolla el comportamiento que predice su conversión a Premium, permitiendo enviar ofertas en el momento oportuno en lugar de generar fricción con ventas prematuras.  

4. Escalabilidad Analítica: El uso de un cubo OLAP es fundamental porque permite realizar consultas multidimensionales de forma eficiente (como se observa en los tiempos de carga reducidos de 19 minutos a 5 segundos para 10 millones de registros), algo imposible de lograr consultando directamente las bases de datos transaccionales.

---

## PROBLEMAS A RESOLVER:

1. Problema: "Ceguera de Marketing en la Expansión Global"  
• El problema: La empresa gasta dinero en publicidad para usuarios que no interactúan o abandonan la app en menos de 24 horas.  
• La solución: El cubo OLAP permite integrar la dimensión dim_ubicacion con los datos de comportamiento. Al realizar un cruce de datos, el sistema identifica qué regiones tienen mayor tasa de retención y cuáles generan usuarios "de paso", permitiendo segmentar las campañas de marketing solo en aquellos países y perfiles que demuestran una alta propensión a la interacción constante.  

2. Problema: "Fuga de Contenido por Desalineación de Gustos (Churn de Contenido)"  
• El problema: Existe una alta tasa de skips (saltos) en las canciones generadas, y se desconoce si el origen del problema es el género, el tema del PDF o la duración de la pieza.  
• La solución: Gracias al ETL de canciones, se tienen atributos definidos como tema, género e idioma. Al cruzar estos datos en Hechos_Interacciones con el Skip Rate Implícito, el sistema permite identificar patrones de rechazo. Por ejemplo, si un tema específico tiene un skip rate inusualmente alto, los analistas pueden ajustar los parámetros de la IA para mejorar la relevancia del contenido generado.  

3. Problema: "Desconexión entre el 'Aha! Moment' y la Suscripción"  
• El problema: La falta de visibilidad sobre el momento preciso en que un usuario gratuito está listo para convertirse en Premium causa fricción, ya que se envían ofertas de venta en momentos inoportunos.  
• La solución: Mediante el análisis de métricas como el Engagement Ratio y la Velocidad de Activación (Time-to-First-Stream), el sistema mapea el comportamiento previo a la suscripción. Al detectar patrones de uso constante y alta interacción (el "Aha! Moment"), el sistema activa el Índice de Propensión Premium, disparando ofertas de suscripción solo cuando el usuario ya ha validado el valor de la plataforma, maximizando la tasa de conversión.
