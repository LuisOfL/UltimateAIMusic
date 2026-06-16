"""
ETL DSS — VERSIÓN ULTRA-OPTIMIZADA v5.2 (CORREGIDA)
==================================================
Fix v5.2:
  - Se corrigió el FATAL CRASH en hechos_adquisicion sustituyendo el ID hardcodeado (1)
    por un mapeo dinámico usando la columna `created_at::DATE` de la tabla origen `usuario`
    hacia su respectivo `id_fecha_hora` en `dim_fecha_hora`.
"""

import io
import os
import time
import psycopg2
import psycopg2.extras
from concurrent.futures import ThreadPoolExecutor, as_completed


HOST     = os.environ.get("DB_HOST",     "seal-users.c180so2u4aci.us-east-2.rds.amazonaws.com")
PORT     = os.environ.get("DB_PORT",     "5432")
USER     = os.environ.get("DB_USER",     "postgres")
PASSWORD = os.environ.get("DB_PASSWORD", "Nomelase123+")

def uri(dbname):
    return f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{dbname}"

def dblink_conn(dbname):
    return f"host={HOST} port={PORT} dbname={dbname} user={USER} password={PASSWORD}"

URI_USUARIOS      = uri("UsersETL")
URI_CANCIONES     = uri("CancionETL")
URI_INTERACCIONES = uri("Interacciones")
URI_OLAP          = uri("OLAP_Operations")


def nueva_conn(uri_: str) -> psycopg2.extensions.connection:
    conn = psycopg2.connect(uri_)
    conn.autocommit = True
    return conn


def ejecutar(uri_: str, sql: str, msg: str = "") -> int:
    t = time.time()
    conn = nueva_conn(uri_)
    try:
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout = 0;")
            cur.execute(sql)
            rows = cur.rowcount
    finally:
        conn.close()
    label = f"{rows:,}" if rows >= 0 else "?"
    print(f"   [OK] {msg} → {label} filas  ({time.time()-t:.1f}s)")
    return rows


def fetch_one(uri_: str, sql: str):
    conn = nueva_conn(uri_)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchone()
    finally:
        conn.close()


def contar(uri_: str, tabla: str) -> int:
    row = fetch_one(uri_, f"SELECT COUNT(*) FROM {tabla};")
    return row[0] if row else 0


def matar_locks_ociosos():
    conn = nueva_conn(URI_OLAP)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = 'OLAP_Operations'
                  AND state IN ('idle in transaction', 'idle in transaction (aborted)')
                  AND query_start < NOW() - INTERVAL '30 seconds';
            """)
            n = cur.rowcount
        if n > 0:
            print(f"   [INFO] Se terminaron {n} conexiones ociosas con locks")
    finally:
        conn.close()


def instalar_dblink():
    print("\n[0] Preparando entorno...")
    matar_locks_ociosos()
    ejecutar(URI_OLAP, "CREATE EXTENSION IF NOT EXISTS dblink;", "dblink instalado")



def limpiar_olap():
    print("\n[1] Limpiando tablas OLAP...")
    tablas_hechos = [
        "hechos_simulaciones", "hechos_data_quality",
        "hechos_interacciones", "hechos_adquisicion",
    ]
    tablas_dims = [
        "dim_cancion", "dim_dispositivo", "dim_fecha_hora",
        "dim_usuario", "dim_ubicacion",
    ]
    conn = nueva_conn(URI_OLAP)
    try:
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout = 0;")
            for t in tablas_hechos + tablas_dims:
                cur.execute(f"TRUNCATE TABLE {t} RESTART IDENTITY CASCADE;")
                print(f"   TRUNCATE {t}")
    finally:
        conn.close()
    print("   [OK] OLAP limpio")



def cargar_dim_escenario():
    print("\n[2] Cargando dim_escenario...")
    escenarios = [
        ("Base",      "Proyección manteniendo la tendencia histórica observada"),
        ("Optimista", "Proyección asumiendo un incremento de actividad del 15% mensual"),
        ("Pesimista", "Proyección asumiendo una caída de actividad del 10% mensual"),
    ]
    conn = nueva_conn(URI_OLAP)
    try:
        with conn.cursor() as cur:
            for nombre, desc in escenarios:
                cur.execute("""
                    INSERT INTO dim_escenario (nombre_escenario, descripcion)
                    SELECT %s, %s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM dim_escenario WHERE nombre_escenario = %s
                    );
                """, (nombre, desc, nombre))
    finally:
        conn.close()
    n = contar(URI_OLAP, "dim_escenario")
    print(f"   [OK] dim_escenario → {n} filas en total")



def _exec_dim(args):
    uri_, sql, msg = args
    t = time.time()
    conn = nueva_conn(uri_)
    try:
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout = 0;")
            cur.execute(sql)
            rows = cur.rowcount
    finally:
        conn.close()
    return msg, rows, time.time() - t


def cargar_dimensiones():
    print("\n[3] Cargando dimensiones (2 fases)...")

    conn_usr = dblink_conn("UsersETL")
    conn_can = dblink_conn("CancionETL")
    conn_int = dblink_conn("Interacciones")

    # ── FASE 1: Todo lo que NO depende de dim_usuario (+ dim_usuario misma) ──
    print("   Fase 1: dim_ubicacion, dim_dispositivo, dim_usuario, dim_fecha_hora (paralelo)...")
    tareas_fase1 = [
        (URI_OLAP, f"""
            INSERT INTO dim_ubicacion (continente, pais, estado)
            SELECT DISTINCT t.continente, t.pais, t.estado
            FROM dblink('{conn_usr}', 'SELECT continente, pais, estado FROM ubicacion')
            AS t(continente VARCHAR, pais VARCHAR, estado VARCHAR)
            ON CONFLICT (continente, pais, estado) DO NOTHING;
        """, "dim_ubicacion"),

        (URI_OLAP, f"""
            INSERT INTO dim_dispositivo (tipo_dispositivo, sistema_operativo, idioma_dispositivo)
            SELECT DISTINCT t.tipo_dispositivo, t.sistema_operativo, t.idioma_dispositivo
            FROM dblink('{conn_int}',
                'SELECT tipo_dispositivo, sistema_operativo, idioma_dispositivo FROM dispositivo')
            AS t(tipo_dispositivo VARCHAR, sistema_operativo VARCHAR, idioma_dispositivo VARCHAR)
            ON CONFLICT (tipo_dispositivo, sistema_operativo, idioma_dispositivo) DO NOTHING;
        """, "dim_dispositivo"),

        (URI_OLAP, f"""
            INSERT INTO dim_usuario (id_usuario, nombre, edad, rango_edad, tipo_membresia)
            SELECT DISTINCT t.id_usuario, t.nombre, t.edad, t.rango_edad, t.tipo_membresia
            FROM dblink('{conn_usr}',
                'SELECT id_usuario, nombre, edad, rango_edad, tipo_membresia FROM usuario')
            AS t(id_usuario VARCHAR, nombre VARCHAR, edad INT,
                 rango_edad VARCHAR, tipo_membresia VARCHAR)
            ON CONFLICT (id_usuario) DO NOTHING;
        """, "dim_usuario"),

        (URI_OLAP, f"""
            INSERT INTO dim_fecha_hora (fecha, dia, mes, trimestre, anio, dia_semana)
            SELECT DISTINCT
                t.fecha, t.dia, t.mes,
                EXTRACT(QUARTER FROM t.fecha)::INT,
                t.anio,
                CASE EXTRACT(DOW FROM t.fecha)
                    WHEN 0 THEN 'Domingo' WHEN 1 THEN 'Lunes'   WHEN 2 THEN 'Martes'
                    WHEN 3 THEN 'Miércoles' WHEN 4 THEN 'Jueves'
                    WHEN 5 THEN 'Viernes'  WHEN 6 THEN 'Sábado'
                END
            FROM dblink('{conn_int}', 'SELECT fecha, dia, mes, anio FROM fecha')
            AS t(fecha DATE, dia INT, mes INT, anio INT)
            ON CONFLICT (fecha) DO NOTHING;
        """, "dim_fecha_hora (histórico)"),
    ]

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(_exec_dim, t): t[2] for t in tareas_fase1}
        for f in as_completed(futures):
            nombre = futures[f]
            try:
                msg, rows, secs = f.result()
                print(f"   [OK] {msg} → {rows:,} filas afectadas  ({secs:.1f}s)")
            except Exception as e:
                print(f"   [ERROR] {nombre}: {e}")


    print("   Fase 2: dim_cancion (requiere dim_usuario lista)...")
    try:
        msg, rows, secs = _exec_dim((URI_OLAP, f"""
            INSERT INTO dim_cancion (id_autor, duracion, idioma, genero, tema)
            SELECT DISTINCT t.id_autor, t.duracion, t.idioma, t.genero, t.tema
            FROM dblink('{conn_can}',
                'SELECT id_autor, duracion, idioma, genero, tema FROM cancion')
            AS t(id_autor VARCHAR, duracion INT, idioma VARCHAR,
                 genero VARCHAR, tema VARCHAR)
            WHERE EXISTS (
                SELECT 1 FROM dim_usuario du WHERE du.id_usuario = t.id_autor
            )
            ON CONFLICT (id_autor, duracion, idioma, genero, tema) DO NOTHING;
        """, "dim_cancion"))
        print(f"   [OK] {msg} → {rows:,} filas afectadas  ({secs:.1f}s)")
    except Exception as e:
        print(f"   [ERROR] dim_cancion: {e}")
        raise


    extender_fechas_futuras(meses=6)
    cargar_usuario_sistema_dss()
    cargar_dispositivo_sistema_dss()


    print("\n   Verificación de conteos reales en dimensiones:")
    dims = ["dim_ubicacion", "dim_dispositivo", "dim_usuario", "dim_cancion", "dim_fecha_hora"]
    for d in dims:
        n = contar(URI_OLAP, d)
        ok = "✓" if n > 0 else "✗ VACÍA"
        print(f"      {ok}  {d}: {n:,} filas")
        if n == 0:
            raise RuntimeError(
                f"ABORT: {d} está vacía tras la carga. "
                "Verificar credenciales dblink y que la tabla fuente existe y tiene datos."
            )
    print("   Todas las dimensiones tienen datos. Continuando...\n")


def extender_fechas_futuras(meses: int = 6):
    sql = f"""
        INSERT INTO dim_fecha_hora (fecha, dia, mes, trimestre, anio, dia_semana)
        SELECT
            d::DATE,
            EXTRACT(DAY     FROM d)::INT,
            EXTRACT(MONTH   FROM d)::INT,
            EXTRACT(QUARTER FROM d)::INT,
            EXTRACT(YEAR    FROM d)::INT,
            CASE EXTRACT(DOW FROM d)
                WHEN 0 THEN 'Domingo' WHEN 1 THEN 'Lunes'   WHEN 2 THEN 'Martes'
                WHEN 3 THEN 'Miércoles' WHEN 4 THEN 'Jueves'
                WHEN 5 THEN 'Viernes'  WHEN 6 THEN 'Sábado'
            END
        FROM generate_series(
            CURRENT_DATE,
            CURRENT_DATE + INTERVAL '{meses} months',
            INTERVAL '1 day'
        ) AS d
        ON CONFLICT (fecha) DO NOTHING;
    """
    ejecutar(URI_OLAP, sql, f"dim_fecha_hora (+{meses} meses proyección)")


def cargar_usuario_sistema_dss():
    conn = nueva_conn(URI_OLAP)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO dim_usuario (id_usuario, nombre, edad, rango_edad, tipo_membresia)
                VALUES ('SYSTEM_DSS', 'Motor de Simulación DSS', 0, 'N/A', 'sistema')
                ON CONFLICT (id_usuario) DO NOTHING;
            """)
    finally:
        conn.close()
    print("   [OK] usuario sintético SYSTEM_DSS")


def cargar_dispositivo_sistema_dss():
    conn = nueva_conn(URI_OLAP)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO dim_dispositivo (tipo_dispositivo, sistema_operativo, idioma_dispositivo)
                VALUES ('Agregado', 'N/A', 'N/A')
                ON CONFLICT (tipo_dispositivo, sistema_operativo, idioma_dispositivo) DO NOTHING;
            """)
    finally:
        conn.close()
    print("   [OK] dispositivo sintético (Agregado)")



INDICES_HECHOS = {
    "hechos_interacciones": [
        ("idx_hechos_inter_usuario", "id_usuario"),
        ("idx_hechos_inter_cancion", "id_cancion"),
        ("idx_hechos_inter_fecha",   "id_fecha_hora"),
    ],
    "hechos_adquisicion": [
        ("idx_hechos_adquis_usuario",   "id_usuario"),
        ("idx_hechos_adquis_ubicacion", "id_ubicacion"),
    ],
}


def quitar_indices_hechos():
    print("\n   Quitando índices secundarios para acelerar carga...")
    for _, indices in INDICES_HECHOS.items():
        for nombre, _ in indices:
            ejecutar(URI_OLAP, f"DROP INDEX IF EXISTS {nombre};", f"drop {nombre}")


def recrear_indices_hechos():
    print("\n   Recreando índices secundarios en paralelo...")
    tareas = [
        (URI_OLAP,
         f"CREATE INDEX IF NOT EXISTS {nombre} ON {tabla}({columna});",
         f"create {nombre}")
        for tabla, indices in INDICES_HECHOS.items()
        for nombre, columna in indices
    ]
    with ThreadPoolExecutor(max_workers=len(tareas)) as pool:
        futures = {pool.submit(_exec_dim, t): t[2] for t in tareas}
        for f in as_completed(futures):
            try:
                msg, rows, secs = f.result()
                print(f"   [OK] {msg}  ({secs:.1f}s)")
            except Exception as e:
                print(f"   [ERROR] índice: {e}")


COPY_BATCH   = 500_000
INSERT_BATCH = 500_000


def _crear_staging(conn_olap):
    with conn_olap.cursor() as cur:
        cur.execute("SET statement_timeout = 0;")
        cur.execute("DROP TABLE IF EXISTS _stg_interacciones;")
        cur.execute("""
            CREATE UNLOGGED TABLE _stg_interacciones (
                id_interaccion      BIGINT,
                id_fecha            BIGINT,
                id_dispositivo      BIGINT,
                id_usuario          VARCHAR(255),
                id_cancion          VARCHAR(255),
                tiempo_reproduccion INT,
                dio_like            BOOLEAN,
                dio_dislike         BOOLEAN,
                descargada          BOOLEAN
            );
        """)
    conn_olap.commit()


def _copy_chunk(conn_olap, rows):
    buf = io.StringIO()
    for r in rows:
        buf.write("\t".join(
            "\\N" if v is None else str(v).replace("\t", " ")
            for v in r
        ) + "\n")
    buf.seek(0)
    with conn_olap.cursor() as cur:
        cur.copy_from(buf, "_stg_interacciones", null="\\N")
    conn_olap.commit()


def _construir_lookups(conn_olap):
    conn_src_str = dblink_conn("Interacciones")
    conn_can_str = dblink_conn("CancionETL")
    conn_usr_str = dblink_conn("UsersETL")

    pasos = [
        ("DROP TABLE IF EXISTS _lkp_fecha;", "drop _lkp_fecha"),
        (f"""
            CREATE UNLOGGED TABLE _lkp_fecha AS
            SELECT src.id_fecha_src, dfh.id_fecha_hora
            FROM dblink('{conn_src_str}', 'SELECT id_fecha, fecha FROM fecha')
                 AS src(id_fecha_src BIGINT, fecha DATE)
            JOIN dim_fecha_hora dfh ON dfh.fecha = src.fecha;
        """, "create _lkp_fecha"),
        ("CREATE INDEX ON _lkp_fecha (id_fecha_src);", "idx _lkp_fecha"),

        ("DROP TABLE IF EXISTS _lkp_dispositivo;", "drop _lkp_dispositivo"),
        (f"""
            CREATE UNLOGGED TABLE _lkp_dispositivo AS
            SELECT src.id_disp_src, dd.id_dispositivo
            FROM dblink('{conn_src_str}',
                'SELECT id_dispositivo, tipo_dispositivo, sistema_operativo, idioma_dispositivo
                 FROM dispositivo')
                 AS src(id_disp_src BIGINT, tipo_dispositivo VARCHAR,
                        sistema_operativo VARCHAR, idioma_dispositivo VARCHAR)
            JOIN dim_dispositivo dd
                ON dd.tipo_dispositivo    = src.tipo_dispositivo
               AND dd.sistema_operativo   = src.sistema_operativo
               AND dd.idioma_dispositivo  = src.idioma_dispositivo;
        """, "create _lkp_dispositivo"),
        ("CREATE INDEX ON _lkp_dispositivo (id_disp_src);", "idx _lkp_dispositivo"),

        ("DROP TABLE IF EXISTS _lkp_cancion;", "drop _lkp_cancion"),
        (f"""
            CREATE UNLOGGED TABLE _lkp_cancion AS
            SELECT src.id_cancion_src, dc.id_cancion
            FROM dblink('{conn_can_str}',
                'SELECT id_cancion, id_autor, duracion, idioma, genero, tema FROM cancion')
                 AS src(id_cancion_src VARCHAR(255), id_autor VARCHAR, duracion INT,
                        idioma VARCHAR, genero VARCHAR, tema VARCHAR)
            JOIN dim_cancion dc
                ON dc.id_autor  = src.id_autor  AND dc.duracion = src.duracion
               AND dc.idioma    = src.idioma    AND dc.genero   = src.genero
               AND dc.tema      = src.tema;
        """, "create _lkp_cancion"),
        ("CREATE INDEX ON _lkp_cancion (id_cancion_src);", "idx _lkp_cancion"),

        ("DROP TABLE IF EXISTS _lkp_usuario;", "drop _lkp_usuario"),
        (f"""
            CREATE UNLOGGED TABLE _lkp_usuario AS
            SELECT du.id_usuario, dub.id_ubicacion
            FROM dblink('{conn_usr_str}',
                'SELECT u.id_usuario, ub.continente, ub.pais, ub.estado
                 FROM usuario u
                 JOIN ubicacion ub ON u.id_ubicacion = ub.id_ubicacion')
                 AS src(id_usuario VARCHAR, continente VARCHAR,
                        pais VARCHAR, estado VARCHAR)
            JOIN dim_usuario   du  ON du.id_usuario    = src.id_usuario
            JOIN dim_ubicacion dub ON dub.continente   = src.continente
                                  AND dub.pais          = src.pais
                                  AND dub.estado        = src.estado;
        """, "create _lkp_usuario"),
        ("CREATE INDEX ON _lkp_usuario (id_usuario);", "idx _lkp_usuario"),
    ]

    for sql, label in pasos:
        t = time.time()
        with conn_olap.cursor() as cur:
            cur.execute("SET statement_timeout = 0;")
            cur.execute(sql)
        conn_olap.commit()
        print(f"      {label}  ({time.time()-t:.1f}s)")

    for tabla in ["_lkp_fecha", "_lkp_dispositivo", "_lkp_cancion", "_lkp_usuario"]:
        with conn_olap.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {tabla};")
            n = cur.fetchone()[0]
        estado = "✓" if n > 0 else "✗ VACÍO — revisar conexión dblink fuente"
        print(f"      {estado} {tabla}: {n:,} filas")
        if n == 0:
            raise RuntimeError(f"ABORT: {tabla} está vacío. Las dimensiones no se cargaron.")


def _limpiar_temporales(conn_olap):
    for t in ["_stg_interacciones", "_lkp_fecha",
              "_lkp_dispositivo", "_lkp_usuario", "_lkp_cancion"]:
        with conn_olap.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {t};")
        conn_olap.commit()


def cargar_hechos_interacciones():
    print("\n[4] Cargando hechos_interacciones (COPY + staging UNLOGGED + lotes)...")
    T = time.time()

    n_ya_cargadas = contar(URI_OLAP, "hechos_interacciones")
    print(f"   Filas ya existentes en hechos_interacciones: {n_ya_cargadas:,}")
    last_src_id = n_ya_cargadas

    conn_src = psycopg2.connect(URI_INTERACCIONES)
    conn_src.autocommit = False

    conn_olap = psycopg2.connect(URI_OLAP)
    conn_olap.autocommit = False

    try:
        with conn_olap.cursor() as cur:
            cur.execute("""
                SET work_mem             = '512MB';
                SET maintenance_work_mem = '1GB';
                SET synchronous_commit   = OFF;
                SET statement_timeout    = 0;
            """)
        conn_olap.commit()

        with conn_olap.cursor() as cur:
            cur.execute("SET session_replication_role = replica;")
        conn_olap.commit()

        _crear_staging(conn_olap)

        cur_src = conn_src.cursor("cur_stream", cursor_factory=psycopg2.extras.DictCursor)
        cur_src.itersize = COPY_BATCH
        cur_src.execute(f"""
            SELECT id_interaccion, id_fecha, id_dispositivo, id_usuario,
                   id_cancion, tiempo_reproduccion, dio_like, dio_dislike, descargada
            FROM interacciones
            WHERE id_interaccion > {last_src_id}
            ORDER BY id_interaccion
        """)

        total_copiadas = 0
        lote_n = 1
        while True:
            rows = cur_src.fetchmany(COPY_BATCH)
            if not rows:
                break
            _copy_chunk(conn_olap, [tuple(r) for r in rows])
            total_copiadas += len(rows)
            vel = total_copiadas / (time.time() - T)
            print(f"   [COPY #{lote_n}] {total_copiadas:,} filas  "
                  f"({time.time()-T:.0f}s | {vel:,.0f} filas/s)")
            lote_n += 1

        cur_src.close()
        conn_src.close()
        print(f"   COPY completado: {total_copiadas:,} filas  ({time.time()-T:.1f}s)")

        if total_copiadas == 0:
            print("   Nada nuevo que cargar.")
            _limpiar_temporales(conn_olap)
            return

        print("   Creando índices en staging...")
        for col in ["id_usuario", "id_cancion", "id_fecha", "id_dispositivo"]:
            with conn_olap.cursor() as cur:
                cur.execute(f"CREATE INDEX ON _stg_interacciones ({col});")
            conn_olap.commit()

        print("   Construyendo lookups de dimensiones...")
        _construir_lookups(conn_olap)
        print(f"   Lookups listos  ({time.time()-T:.1f}s)")

        with conn_olap.cursor() as cur:
            cur.execute(
                "SELECT id_fecha_hora FROM dim_fecha_hora WHERE fecha = CURRENT_DATE;"
            )
            row = cur.fetchone()
        id_fecha_log = row[0] if row else 1

        print(f"   Insertando en lotes de {INSERT_BATCH:,}...")
        total_ok = 0
        total_dq = 0
        offset   = 0

        while True:
            with conn_olap.cursor() as cur:
                cur.execute(f"""
                    WITH page AS (
                        SELECT
                            s.id_interaccion,
                            s.id_fecha, s.id_dispositivo,
                            s.id_usuario, s.id_cancion,
                            s.tiempo_reproduccion,
                            s.dio_like, s.dio_dislike, s.descargada,
                            lf.id_fecha_hora,
                            lu.id_usuario   AS du_id,
                            lu.id_ubicacion AS du_ubicacion,
                            ld.id_dispositivo AS dd_id,
                            lc.id_cancion   AS dc_id
                        FROM _stg_interacciones s
                        LEFT JOIN _lkp_fecha       lf ON lf.id_fecha_src  = s.id_fecha
                        LEFT JOIN _lkp_dispositivo ld ON ld.id_disp_src   = s.id_dispositivo
                        LEFT JOIN _lkp_usuario     lu ON lu.id_usuario    = s.id_usuario
                        LEFT JOIN _lkp_cancion     lc ON lc.id_cancion_src = s.id_cancion
                        ORDER BY s.id_interaccion
                        LIMIT {INSERT_BATCH} OFFSET {offset}
                    ),
                    ins_ok AS (
                        INSERT INTO hechos_interacciones
                            (id_fecha_hora, id_usuario, id_cancion,
                             id_ubicacion, id_dispositivo,
                             tiempo_reproduccion, dio_like, dio_dislike, descargada)
                        SELECT
                            id_fecha_hora, du_id, dc_id,
                            du_ubicacion, dd_id,
                            tiempo_reproduccion,
                            dio_like::SMALLINT,
                            dio_dislike::SMALLINT,
                            descargada::SMALLINT
                        FROM page
                        WHERE id_fecha_hora IS NOT NULL
                          AND du_id         IS NOT NULL
                          AND dc_id         IS NOT NULL
                          AND du_ubicacion  IS NOT NULL
                          AND dd_id         IS NOT NULL
                        RETURNING 1
                    ),
                    ins_dq AS (
                        INSERT INTO hechos_data_quality
                            (id_fecha_hora, entidad_afectada,
                             tipo_error, detalle_error, severidad)
                        SELECT
                            {id_fecha_log},
                            'hechos_interacciones',
                            CASE
                                WHEN id_fecha_hora IS NULL THEN 'fecha_no_encontrada'
                                WHEN du_id         IS NULL THEN 'usuario_no_encontrado'
                                WHEN dc_id         IS NULL THEN 'cancion_no_encontrada'
                                WHEN du_ubicacion  IS NULL THEN 'ubicacion_no_encontrada'
                                WHEN dd_id         IS NULL THEN 'dispositivo_no_encontrado'
                            END,
                            format('id=%s f=%s u=%s c=%s d=%s',
                                   id_interaccion, id_fecha,
                                   id_usuario, id_cancion, id_dispositivo),
                            3
                        FROM page
                        WHERE id_fecha_hora IS NULL OR du_id IS NULL
                           OR dc_id IS NULL OR du_ubicacion IS NULL OR dd_id IS NULL
                        RETURNING 1
                    )
                    SELECT
                        (SELECT COUNT(*) FROM page)   AS n_page,
                        (SELECT COUNT(*) FROM ins_ok) AS n_ok,
                        (SELECT COUNT(*) FROM ins_dq) AS n_dq;
                """)
                n_page, n_ok, n_dq = cur.fetchone()
            conn_olap.commit()

            total_ok += n_ok
            total_dq += n_dq
            offset   += n_page
            vel       = offset / (time.time() - T) if (time.time() - T) > 0 else 0

            print(f"   [INSERT offset={offset:,}] "
                  f"OK {total_ok:,} | DQ {total_dq:,} | "
                  f"{vel:,.0f} filas/s | {time.time()-T:.0f}s")

            if n_page < INSERT_BATCH:
                break

    finally:
        try:
            with conn_olap.cursor() as cur:
                cur.execute("SET session_replication_role = DEFAULT;")
            conn_olap.commit()
            _limpiar_temporales(conn_olap)
        except Exception:
            pass
        conn_olap.close()

    mins = (time.time() - T) / 60
    print(f"\n   hechos_interacciones COMPLETO: "
          f"{total_ok:,} OK | {total_dq:,} DQ  ({mins:.1f} min)")



def cargar_hechos_adquisicion():
    print("\n[5] Cargando hechos_adquisicion (incremental dinámico)...")
    conn_usr = dblink_conn("UsersETL")
    

    ejecutar(URI_OLAP, f"""
        INSERT INTO hechos_adquisicion
            (id_fecha_hora, id_usuario, id_ubicacion, id_dispositivo, usuario_registrado)
        SELECT
            COALESCE(dfh.id_fecha_hora, (SELECT id_fecha_hora FROM dim_fecha_hora ORDER BY fecha LIMIT 1)),
            du.id_usuario,
            dub.id_ubicacion,
            (SELECT id_dispositivo FROM dim_dispositivo WHERE tipo_dispositivo = 'Agregado' LIMIT 1),
            1
        FROM dblink('{conn_usr}',
            'SELECT u.id_usuario, u.created_at, ub.continente, ub.pais, ub.estado
             FROM usuario u
             JOIN ubicacion ub ON u.id_ubicacion = ub.id_ubicacion')
        AS src(id_usuario VARCHAR, created_at TIMESTAMP, continente VARCHAR, pais VARCHAR, estado VARCHAR)
        JOIN dim_usuario   du  ON du.id_usuario   = src.id_usuario
        JOIN dim_ubicacion dub ON dub.continente  = src.continente
                               AND dub.pais        = src.pais
                               AND dub.estado      = src.estado
        LEFT JOIN dim_fecha_hora dfh ON dfh.fecha = src.created_at::DATE
        WHERE NOT EXISTS (
            SELECT 1 FROM hechos_adquisicion ha WHERE ha.id_usuario = du.id_usuario
        );
    """, "hechos_adquisicion")


def cargar_hechos_simulaciones(meses_proyeccion: int = 3):
    print(f"\n[6] Re-calculando hechos_simulaciones ({meses_proyeccion} meses)...")
    ejecutar(URI_OLAP,
        "TRUNCATE TABLE hechos_simulaciones RESTART IDENTITY;",
        "Limpieza previa")

    sql = f"""
    INSERT INTO hechos_simulaciones
        (id_escenario, id_ubicacion, id_fecha_hora, id_usuario,
         id_dispositivo, kpi_proyectado_valor, metodo_proyeccion)
    WITH base AS (
        SELECT m.id_ubicacion, AVG(m.conteo_mensual) AS kpi_base
        FROM (
            SELECT hi.id_ubicacion, dfh.anio, dfh.mes,
                   COUNT(*) AS conteo_mensual
            FROM hechos_interacciones hi
            JOIN dim_fecha_hora dfh ON dfh.id_fecha_hora = hi.id_fecha_hora
            WHERE dfh.fecha >= CURRENT_DATE - INTERVAL '3 months'
            GROUP BY hi.id_ubicacion, dfh.anio, dfh.mes
        ) m
        GROUP BY m.id_ubicacion
    ),
    escenarios AS (
        SELECT id_escenario, nombre_escenario,
               CASE nombre_escenario
                   WHEN 'Optimista' THEN 1.15
                   WHEN 'Pesimista' THEN 0.90
                   ELSE 1.00
               END AS factor_mensual
        FROM dim_escenario
    ),
    futuro AS (
        SELECT id_fecha_hora, fecha
        FROM dim_fecha_hora
        WHERE fecha > CURRENT_DATE AND dia = 1
        ORDER BY fecha
        LIMIT {meses_proyeccion}
    )
    SELECT
        e.id_escenario,
        b.id_ubicacion,
        f.id_fecha_hora,
        (SELECT id_usuario FROM dim_usuario WHERE id_usuario = 'SYSTEM_DSS' LIMIT 1),
        (SELECT id_dispositivo FROM dim_dispositivo
            WHERE tipo_dispositivo   = 'Agregado'
              AND sistema_operativo  = 'N/A'
              AND idioma_dispositivo = 'N/A'
            LIMIT 1),
        ROUND(
            b.kpi_base * POWER(
                e.factor_mensual,
                (EXTRACT(YEAR  FROM f.fecha) - EXTRACT(YEAR  FROM CURRENT_DATE)) * 12
              + (EXTRACT(MONTH FROM f.fecha) - EXTRACT(MONTH FROM CURRENT_DATE))
            ), 2),
        'tasa_crecimiento_simple'
    FROM base b
    CROSS JOIN escenarios e
    CROSS JOIN futuro f;
    """
    ejecutar(URI_OLAP, sql, "hechos_simulaciones")


# ─────────────────────────────────────────────────────────────────
# PASO 7: ANALYZE
# ─────────────────────────────────────────────────────────────────
def analizar_tablas():
    print("\n[7] ANALYZE en tablas de hechos (en paralelo)...")
    tablas = [
        "hechos_interacciones", "hechos_adquisicion",
        "hechos_simulaciones",  "hechos_data_quality",
    ]
    with ThreadPoolExecutor(max_workers=len(tablas)) as pool:
        futures = {pool.submit(ejecutar, URI_OLAP, f"ANALYZE {t};", f"ANALYZE {t}"): t for t in tablas}
        for f in as_completed(futures):
            t = futures[f]
            try:
                f.result()
            except Exception as e:
                print(f"   [ERROR] ANALYZE {t}: {e}")



if __name__ == "__main__":
    t_inicio = time.time()
    print("==================================================")
    print("      INICIANDO PIPELINE ETL OPTIMIZADO V5.2      ")
    print("==================================================")
    
    try:
        instalar_dblink()

        
        cargar_dim_escenario()
        cargar_dimensiones()
        
        quitar_indices_hechos()
        
        cargar_hechos_interacciones()
        cargar_hechos_adquisicion()
        cargar_hechos_simulaciones(meses_proyeccion=3)
        
        recrear_indices_hechos()
        analizar_tablas()
        
        mins_totales = (time.time() - t_inicio) / 60
        print("==================================================")
        print(f"   ETL EJECUTADO EXITOSAMENTE EN: {mins_totales:.2f} min")
        print("==================================================")
    except Exception as err:
        print("\n[FATAL CRASH] El proceso de ETL se interrumpió:")
        print(f"Detalle del error: {err}")