import time
import pandas as pd
import numpy as np
import joblib
import os
import re
import sys
import logging
from collections import deque
from tensorflow.keras.models import load_model
from prometheus_client import start_http_server, Counter, Gauge
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import warnings

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN ---
LOG_FILE_PATH = '/var/log/apache2/access.log'
INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN', 'my-super-secret-token')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG', 'my-org')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', 'network_traffic')
TIMESTEPS = 10 
UMBRAL = 0.15

logger.info("=" * 60)
logger.info("INICIANDO SISTEMA DE DETECCIÓN DE ANOMALÍAS EN LOGS")
logger.info("=" * 60)
logger.info(f"INFLUXDB_URL: {INFLUXDB_URL}")
logger.info(f"INFLUXDB_ORG: {INFLUXDB_ORG}")
logger.info(f"INFLUXDB_BUCKET: {INFLUXDB_BUCKET}")
logger.info(f"LOG_FILE_PATH: {LOG_FILE_PATH}")
logger.info(f"TIMESTEPS: {TIMESTEPS}")
logger.info(f"UMBRAL: {UMBRAL}")
logger.info("=" * 60)

# --- CARGA DE ARTEFACTOS ---
logger.info("[*] Cargando modelo y transformadores...")
try:
    # Verificar existencia de archivos
    required_files = [
        'modelo_logs_1.h5',
        'scaler_logs_1.joblib',
        'encoders_logs_1.joblib'
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            logger.error(f"[!] ERROR CRÍTICO: No se encuentra el archivo {file}")
            logger.error(f"    Archivos en directorio actual: {os.listdir('.')}")
            sys.exit(1)
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        modelo = load_model('modelo_logs_1.h5', compile=False)
        scaler = joblib.load('scaler_logs_1.joblib')
        encoders = joblib.load('encoders_logs_1.joblib')
    
    logger.info("[✓] Artefactos cargados exitosamente.")
    logger.info(f"    - Modelo: {modelo}")
    logger.info(f"    - Encoders disponibles: {list(encoders.keys())}")
    
    # NUEVO: Extraer nombres de características del scaler
    if hasattr(scaler, 'feature_names_in_'):
        FEATURE_NAMES = list(scaler.feature_names_in_)
        logger.info(f"    - Feature names detectados: {FEATURE_NAMES}")
    else:
        # Fallback: orden esperado de características
        FEATURE_NAMES = ['ip', 'method', 'url', 'http_version', 'referer', 
                        'user_agent', 'tls_version', 'cipher_suite', 'log_source',
                        'status_code', 'response_size']
        logger.warning(f"    - Feature names no encontrados, usando orden por defecto")
        
except Exception as e:
    logger.error(f"[!] Error crítico cargando archivos: {e}")
    logger.error(f"    Tipo de error: {type(e).__name__}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)

# --- CONEXIÓN INFLUXDB ---
logger.info("[*] Conectando a InfluxDB...")
try:
    influx_client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    write_api = influx_client.write_api(write_options=SYNCHRONOUS)
    
    # Verificar conexión
    health = influx_client.health()
    logger.info(f"[✓] Conexión a InfluxDB exitosa - Estado: {health.status}")
except Exception as e:
    logger.error(f"[!] Error conectando a InfluxDB: {e}")
    logger.warning("    Continuando sin InfluxDB...")
    write_api = None

# --- MÉTRICAS PROMETHEUS ---
logger.info("[*] Configurando métricas Prometheus...")
PAQUETES_PROCESADOS = Counter('logs_procesados_total', 'Total de líneas de log analizadas')
ANOMALIA_SCORE = Gauge('log_anomalia_score', 'Score de anomalía del último log')
ANOMALIA_DETECTADA = Gauge('log_anomalia_detectada', '1 si es anomalía, 0 si no')

# Buffer
ventana_deslizante = deque(maxlen=TIMESTEPS)

def safe_transform(encoder, value):
    """Maneja valores nuevos asignándolos a clase 'desconocida' (0)"""
    try:
        return encoder.transform([str(value)])[0]
    except ValueError:
        return 0 

def parse_apache_log(line):
    """Parsea logs de Apache Combined Format usando Regex"""
    regex = r'^(\S+) \S+ \S+ \[(.*?)\] "(\S+) (\S+) (\S+)" (\d+) (\d+|-) "(.*?)" "(.*?)"'
    
    match = re.match(regex, line)
    if not match:
        return None
    
    data = match.groups()
    
    size = data[6]
    if size == '-':
        size = 0
    else:
        size = int(size)

    return {
        'ip': data[0],
        'timestamp': data[1],
        'method': data[2],
        'url': data[3],
        'http_version': data[4],
        'status_code': int(data[5]),
        'response_size': size,
        'referer': data[7],
        'user_agent': data[8],
        'tls_version': '-', 
        'cipher_suite': '-',
        'log_source': 'apache_access_log'
    }

def procesar_log(raw_line):
    parsed_data = parse_apache_log(raw_line)
    
    if not parsed_data: 
        return

    try:
        # SOLUCIÓN: Crear DataFrame con nombres de columnas
        features_dict = {}
        
        # Procesar Columnas Categóricas
        cat_cols = ['ip', 'method', 'url', 'http_version', 'referer', 
                    'user_agent', 'tls_version', 'cipher_suite', 'log_source']
        
        for col in cat_cols:
            val = str(parsed_data.get(col, '-'))
            if col in encoders:
                val_encoded = safe_transform(encoders[col], val)
            else:
                val_encoded = 0
            features_dict[col] = val_encoded

        # Procesar Columnas Numéricas
        num_cols = ['status_code', 'response_size']
        for col in num_cols:
            val = parsed_data.get(col, 0)
            features_dict[col] = float(val)

        # CAMBIO PRINCIPAL: Crear DataFrame en lugar de numpy array
        df_row = pd.DataFrame([features_dict])
        
        # Asegurar orden correcto de columnas
        df_row = df_row[FEATURE_NAMES]
        
        # Escalar usando DataFrame (elimina el warning)
        vector_scaled = scaler.transform(df_row)

        # Añadir a ventana temporal
        ventana_deslizante.append(vector_scaled[0])

        # Predicción cuando la ventana está llena
        if len(ventana_deslizante) == TIMESTEPS:
            secuencia = np.array([list(ventana_deslizante)])
            
            reconstruccion = modelo.predict(secuencia, verbose=0)
            
            mae = np.mean(np.abs(reconstruccion - secuencia))
            
            es_anomalia = mae > UMBRAL

            # Métricas
            PAQUETES_PROCESADOS.inc()
            ANOMALIA_SCORE.set(mae)
            ANOMALIA_DETECTADA.set(1 if es_anomalia else 0)

            if es_anomalia:
                logger.warning(f"🚨 ANOMALÍA: IP={parsed_data['ip']} URL={parsed_data['url']} Score={mae:.4f}")
            
            # Enviar a InfluxDB
            if write_api:
                try:
                    p = Point("web_traffic") \
                        .tag("ip", str(parsed_data['ip'])) \
                        .tag("method", str(parsed_data['method'])) \
                        .tag("status", str(parsed_data['status_code'])) \
                        .field("score_anomalia", float(mae)) \
                        .field("is_anomaly", int(es_anomalia)) \
                        .field("response_size", int(parsed_data['response_size'])) \
                        .field("url", str(parsed_data['url']))
                    
                    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=p)
                except Exception as e:
                    logger.error(f"Error escribiendo a InfluxDB: {e}")

    except Exception as e:
        logger.error(f"[!] Error procesando log: {e}")
        import traceback
        logger.error(traceback.format_exc())

def tail_file(filepath):
    """Lee el archivo en modo 'tail -f'"""
    retry_count = 0
    max_retries = 30
    
    while not os.path.exists(filepath):
        logger.warning(f"[*] Esperando archivo {filepath}... ({retry_count}/{max_retries})")
        time.sleep(2)
        retry_count += 1
        if retry_count >= max_retries:
            logger.error(f"[!] TIMEOUT: El archivo {filepath} no apareció después de {max_retries * 2} segundos")
            sys.exit(1)

    logger.info(f"[✓] Archivo encontrado: {filepath}")
    
    file = open(filepath, 'r')
    file.seek(0, 2)  # Ir al final
    logger.info(f"[✓] Escuchando logs de Apache en: {filepath}")
    
    while True:
        line = file.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line

if __name__ == '__main__':
    try:
        logger.info("[*] Iniciando servidor HTTP Prometheus en puerto 8000...")
        start_http_server(8000)
        logger.info("[✓] Servidor Prometheus iniciado en http://0.0.0.0:8000")
        
        logger.info("[*] Iniciando monitoreo de logs...")
        
        # Iniciar bucle principal
        for line in tail_file(LOG_FILE_PATH):
            procesar_log(line)
            
    except KeyboardInterrupt:
        logger.info("\n[*] Deteniendo capturador...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"[!] Error fatal: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)