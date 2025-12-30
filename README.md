# 🛡️ Sistema de Detección de Anomalías en Logs Web

Sistema automatizado de detección de anomalías en logs de Apache mediante **Deep Learning (LSTM Autoencoder)**. Desarrollado para el Sistema de Gobierno Digital.

**Stack**: Python + TensorFlow + Docker + InfluxDB + Prometheus + Grafana

---

## 📋 Requisitos Previos

| Componente | Versión | Verificar |
|------------|---------|-----------|
| Ubuntu/Debian | 20.04+ | `lsb_release -a` |
| Docker | 20.10+ | `docker --version` |
| Docker Compose | 1.29+ | `docker-compose --version` |
| RAM | 4 GB mínimo | `free -h` |
| Espacio en disco | 5 GB libre | `df -h` |

---

## 🚀 Despliegue Completo

### Paso 1: Instalar y Configurar Apache

```bash
# Verificar si Apache está instalado
apache2 -v

# Si no está instalado, instalarlo
sudo apt update
sudo apt install apache2 -y

# Iniciar y habilitar Apache
sudo systemctl start apache2
sudo systemctl enable apache2

# Verificar estado
sudo systemctl status apache2

# Verificar que Apache está corriendo
curl -I http://localhost
# Debe responder: HTTP/1.1 200 OK
```

#### Verificar Logs de Apache

```bash
# Verificar que el archivo de logs existe
ls -lh /var/log/apache2/access.log

# Ver últimas líneas del log
sudo tail -f /var/log/apache2/access.log

# Si el archivo no existe o está vacío, generar tráfico
curl http://localhost/
curl http://localhost/index.html
curl http://localhost/test

# Verificar que se generaron logs
sudo tail -5 /var/log/apache2/access.log
```

#### Dar Permisos al Archivo de Logs

```bash
# El contenedor Docker necesita leer el archivo
sudo chmod 644 /var/log/apache2/access.log

# Verificar permisos
ls -l /var/log/apache2/access.log
# Debe mostrar: -rw-r--r--
```

### Paso 2: Instalar Docker

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Agregar usuario al grupo docker
sudo usermod -aG docker $USER
newgrp docker

# Instalar Docker Compose
sudo apt install docker-compose -y

# Verificar instalación
docker --version
docker-compose --version
```

### Paso 3: Clonar el Proyecto

```bash
# Clonar repositorio
git clone https://github.com/KENETGOD/SFA-MODELO-LSTM-ANOMALIAS.git
cd SFA-MODELO-LSTM-ANOMALIAS/

# Verificar archivos del modelo
ls -lh modelo_logs_1.h5 scaler_logs_1.joblib encoders_logs_1.joblib
```

### Paso 4: Configurar Ruta de Logs

```bash
# Editar docker-compose.yml para apuntar a tus logs de Apache
nano docker-compose.yml

# Verificar la línea de volúmenes del servicio 'capturador':
# volumes:
#   - /var/log/apache2/access.log:/var/log/apache2/access.log:ro

# Si tu Apache está en otra ubicación, cambiar la ruta:
# - /tu/ruta/personalizada/access.log:/var/log/apache2/access.log:ro

# Guardar y cerrar (Ctrl+X, Y, Enter)
```

### Paso 5: Construir y Levantar Servicios

```bash
# Construir imágenes y levantar todos los servicios
docker-compose up -d --build

# Esperar 30 segundos a que todo inicie
sleep 30

# Verificar estado de servicios
docker-compose ps
```

**Salida esperada**:
```
NAME          STATUS        PORTS
capturador    Up            0.0.0.0:8000->8000/tcp
grafana       Up            0.0.0.0:3000->3000/tcp
influxdb      Up (healthy)  0.0.0.0:8086->8086/tcp
prometheus    Up            0.0.0.0:9090->9090/tcp
```

### Paso 4: Verificar Conectividad

```bash
# Verificar todos los servicios
curl -f http://localhost:8086/health        # InfluxDB
curl -f http://localhost:9090/-/healthy    # Prometheus
curl -f http://localhost:3000/api/health   # Grafana
curl -f http://localhost:8000/metrics      # Capturador

# Todos deben responder HTTP 200
```

### Paso 5: Ver Logs en Tiempo Real

```bash
# Ver logs del capturador
docker-compose logs -f capturador

# Deberías ver:
# [✓] Artefactos cargados exitosamente
# [✓] Conexión a InfluxDB exitosa
# [✓] Servidor Prometheus iniciado en http://0.0.0.0:8000
# [✓] Escuchando logs de Apache en: /var/log/apache2/access.log
```

---

## 📊 Configurar Grafana

### Acceso Inicial

```bash
# Abrir navegador en:
http://localhost:3000

# Credenciales:
# Usuario: admin
# Password: admin
# (cambiar al primer login)
```

### Agregar Data Sources

#### Prometheus

```bash
# En Grafana:
# 1. Menú lateral → ⚙️ Configuration → Data Sources → Add data source
# 2. Seleccionar "Prometheus"
# 3. Configurar:
```

```yaml
Name: Prometheus
URL: http://prometheus:9090
Access: Server (default)
```

```bash
# 4. Click "Save & Test" → debe decir ✅ "Data source is working"
```

#### InfluxDB

```bash
# En Grafana:
# 1. Data Sources → Add data source → Seleccionar "InfluxDB"
# 2. Configurar:
```

```yaml
Name: InfluxDB
Query Language: Flux           # ⚠️ IMPORTANTE: No usar InfluxQL

HTTP:
URL: http://influxdb:8086
Access: Server (default)

InfluxDB Details:
Organization: my-org
Token: my-super-secret-token
Default Bucket: network_traffic
```

```bash
# 3. Click "Save & Test" → debe decir ✅ "datasource is working"
```

### Crear Dashboard Simple

```bash
# En Grafana:
# 1. Menú lateral → + Dashboards → New Dashboard → Add visualization
# 2. Seleccionar data source "Prometheus"
# 3. En la query, escribir: log_anomalia_detectada
# 4. Panel type: Stat
# 5. Click "Apply"
```

---

## 🧪 Generar Tráfico de Prueba

### Opción 1: Tráfico Real en Apache (Recomendado)

```bash
# Generar tráfico web normal
for i in {1..50}; do
  curl http://localhost/ > /dev/null 2>&1
  curl http://localhost/index.html > /dev/null 2>&1
  sleep 0.5
done

# Verificar que se generaron logs
sudo tail -10 /var/log/apache2/access.log

# Generar tráfico variado
curl http://localhost/test.html
curl http://localhost/images/logo.png
curl -X POST http://localhost/api/data
curl http://localhost/admin
curl http://localhost/favicon.ico

# Ver logs del capturador procesando
docker-compose logs -f capturador
```

### Opción 2: Simular Tráfico Anómalo

```bash
# Intentar acceder a archivos sensibles (404s)
curl http://localhost/admin.php
curl http://localhost/.env
curl http://localhost/wp-admin
curl http://localhost/phpmyadmin
curl http://localhost/.git/config

# Simular user agents sospechosos
curl -A "sqlmap/1.0" http://localhost/
curl -A "nikto/2.1.5" http://localhost/admin
curl -A "nmap scripting engine" http://localhost/

# Verificar detección
docker-compose logs capturador | grep "ANOMALÍA"
```

### Opción 3: Insertar Logs Directamente (Para Pruebas Rápidas)

```bash
# Logs Normales

```bash
# Generar 100 logs normales
for i in {1..100}; do
  docker-compose exec capturador bash -c "echo '192.168.1.$i - - [$(date -u +%d/%b/%Y:%H:%M:%S) +0000] \"GET /index.html HTTP/1.1\" 200 $((1000 + RANDOM % 3000)) \"-\" \"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0\"' >> /var/log/apache2/access.log"
  sleep 0.5
done
```

### Logs Anómalos (Ataques)

```bash
# Simular ataques SQL Injection
for i in {1..20}; do
  docker-compose exec capturador bash -c "echo '192.168.1.$i - - [$(date -u +%d/%b/%Y:%H:%M:%S) +0000] \"POST /admin.php HTTP/1.1\" 404 0 \"-\" \"sqlmap/1.0\"' >> /var/log/apache2/access.log"
  sleep 0.3
done

# Simular escaneo de directorios
for i in {1..15}; do
  docker-compose exec capturador bash -c "echo '192.168.1.$i - - [$(date -u +%d/%b/%Y:%H:%M:%S) +0000] \"GET /.env HTTP/1.1\" 404 0 \"-\" \"curl/7.68.0\"' >> /var/log/apache2/access.log"
  sleep 0.4
done

# Simular tráfico con response size anormal
for i in {1..10}; do
  docker-compose exec capturador bash -c "echo '192.168.1.$i - - [$(date -u +%d/%b/%Y:%H:%M:%S) +0000] \"GET /download.zip HTTP/1.1\" 200 $((50000 + RANDOM % 50000)) \"-\" \"wget/1.20.3\"' >> /var/log/apache2/access.log"
  sleep 0.6
done
```

### Ver Resultados

```bash
# Ver logs del capturador en tiempo real
docker-compose logs -f capturador

# Buscar anomalías detectadas
docker-compose logs capturador | grep "ANOMALÍA"

# Verificar métricas en Prometheus
curl -s http://localhost:9090/api/v1/query?query=log_anomalia_detectada | jq

# Ver en Grafana
# http://localhost:3000
```

---

## 🔧 Comandos de Gestión

### Ver Estado

```bash
# Estado de todos los servicios
docker-compose ps

# Logs de todos los servicios
docker-compose logs

# Logs de un servicio específico
docker-compose logs capturador
docker-compose logs grafana
docker-compose logs influxdb
docker-compose logs prometheus

# Logs en tiempo real
docker-compose logs -f capturador

# Últimas 50 líneas
docker-compose logs --tail=50 capturador
```

### Reiniciar Servicios

```bash
# Reiniciar un servicio
docker-compose restart capturador

# Reiniciar todos
docker-compose restart

# Reconstruir un servicio
docker-compose up -d --build capturador

# Reconstruir todos
docker-compose up -d --build
```

### Detener Sistema

```bash
# Detener servicios (conserva datos)
docker-compose stop

# Detener y eliminar contenedores (conserva volúmenes)
docker-compose down

# Eliminar TODO incluyendo datos ⚠️
docker-compose down -v
```

### Ver Recursos

```bash
# Uso de CPU y RAM por contenedor
docker stats

# Espacio en disco usado
docker system df

# Información detallada de un contenedor
docker-compose exec capturador top
```

---

## 🔍 Verificación y Diagnóstico

### Verificar que Todo Funciona

```bash
# Script de verificación completo
echo "=== Verificando Apache ==="
curl -I http://localhost 2>&1 | grep "HTTP" && echo "✓ Apache OK" || echo "✗ Apache FAIL"
ls -l /var/log/apache2/access.log && echo "✓ Logs existen" || echo "✗ Logs no existen"

echo -e "\n=== Verificando Servicios Docker ==="
docker-compose ps

echo -e "\n=== Verificando InfluxDB ==="
curl -f http://localhost:8086/health 2>/dev/null && echo "✓ InfluxDB OK" || echo "✗ InfluxDB FAIL"

echo -e "\n=== Verificando Prometheus ==="
curl -f http://localhost:9090/-/healthy 2>/dev/null && echo "✓ Prometheus OK" || echo "✗ Prometheus FAIL"

echo -e "\n=== Verificando Grafana ==="
curl -f http://localhost:3000/api/health 2>/dev/null && echo "✓ Grafana OK" || echo "✗ Grafana FAIL"

echo -e "\n=== Verificando Capturador ==="
curl -f http://localhost:8000/metrics 2>/dev/null && echo "✓ Capturador OK" || echo "✗ Capturador FAIL"

echo -e "\n=== Verificando Métricas ==="
LOGS_COUNT=$(curl -s http://localhost:9090/api/v1/query?query=logs_procesados_total 2>/dev/null | grep -o '"value":\[[^]]*\]' | grep -o '[0-9.]*' | tail -1)
echo "Logs procesados: $LOGS_COUNT"

echo -e "\n=== Verificando Acceso a Logs desde Contenedor ==="
docker-compose exec capturador cat /var/log/apache2/access.log | head -2 > /dev/null 2>&1 && echo "✓ Capturador puede leer logs" || echo "✗ Capturador NO puede leer logs"
```

### Problemas Comunes

#### Apache no está instalado o no funciona

```bash
# Verificar si Apache está corriendo
sudo systemctl status apache2

# Si está detenido, iniciarlo
sudo systemctl start apache2

# Verificar que responde
curl -I http://localhost

# Si no responde, revisar logs de Apache
sudo tail -50 /var/log/apache2/error.log

# Reinstalar Apache si es necesario
sudo apt purge apache2 -y
sudo apt install apache2 -y
sudo systemctl start apache2
```

#### Logs de Apache vacíos o no existen

```bash
# Verificar que el archivo existe
ls -l /var/log/apache2/access.log

# Si no existe, generar tráfico
curl http://localhost/

# Si sigue sin existir, verificar configuración de Apache
sudo nano /etc/apache2/sites-available/000-default.conf

# Debe tener estas líneas:
# CustomLog ${APACHE_LOG_DIR}/access.log combined

# Reiniciar Apache
sudo systemctl restart apache2

# Generar tráfico nuevamente
curl http://localhost/
```

#### Capturador no puede leer los logs

```bash
# Verificar permisos del archivo
ls -l /var/log/apache2/access.log

# Dar permisos de lectura
sudo chmod 644 /var/log/apache2/access.log

# Verificar desde el contenedor
docker-compose exec capturador cat /var/log/apache2/access.log | head -5

# Si dice "No such file", verificar el volumen en docker-compose.yml
docker-compose exec capturador ls -l /var/log/apache2/
```

#### Servicio no inicia

```bash
# Ver el error específico
docker-compose logs capturador

# Si es problema de archivos del modelo
ls -lh modelo_logs_*.{h5,joblib}
# Si faltan, descargarlos o copiarlos

# Reconstruir
docker-compose up -d --build capturador
```

#### Puerto en uso

```bash
# Ver qué está usando el puerto
sudo lsof -i :3000
sudo lsof -i :8000
sudo lsof -i :8086
sudo lsof -i :9090

# Matar proceso
sudo kill -9 <PID>

# O cambiar puerto en docker-compose.yml
```

#### No se detectan logs

```bash
# Verificar archivo de logs
docker-compose exec capturador ls -l /var/log/apache2/

# Crear log manualmente
docker-compose exec capturador bash -c 'echo "192.168.1.1 - - [22/Dec/2025:10:00:00 +0000] \"GET / HTTP/1.1\" 200 1234 \"-\" \"Mozilla/5.0\"" >> /var/log/apache2/access.log'

# Ver si se procesó
docker-compose logs --tail=10 capturador
```

---

## 🎓 Entrenar Modelo Personalizado

### Preparar Datos

```bash
# Tu CSV debe tener estas columnas:
# timestamp,ip,method,url,http_version,status_code,response_size,referer,user_agent,tls_version,cipher_suite,log_source
```

### Entrenar

```bash
# Instalar dependencias
pip install -r requirements.txt

# Editar archivo de configuración
nano MODELO_LOGS2.py
# Cambiar línea 58: DATA_FILE = 'tus_logs.csv'

# Ejecutar entrenamiento
python3 MODELO_LOGS2.py

# Archivos generados:
# - modelo_logs_1.h5
# - scaler_logs_1.joblib
# - encoders_logs_1.joblib
# - grafico_entrenamiento_1.png
```

### Usar Nuevo Modelo

```bash
# Detener sistema
docker-compose down

# Reemplazar archivos
cp modelo_logs_3.h5 scaler_logs_3.joblib encoders_logs_3.joblib ./

# Reconstruir y levantar
docker-compose up -d --build
```

---

## ⚙️ Configuración Avanzada

### Cambiar Umbral de Detección

```bash
# Editar capturador.py
nano capturador.py

# Línea 22 - Cambiar:
UMBRAL = 0.15  # Valores recomendados:
# 0.05-0.08: Muy estricto (logs de gobierno)
# 0.10-0.15: Balanceado (por defecto)
# 0.20-0.25: Permisivo

# Aplicar cambios
docker-compose up -d --build capturador
```

### Cambiar Credenciales

```bash
# Editar docker-compose.yml
nano docker-compose.yml

# Cambiar estas líneas:
# DOCKER_INFLUXDB_INIT_PASSWORD=tu-password-seguro
# DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=tu-token-seguro
# INFLUXDB_TOKEN=tu-token-seguro (mismo del anterior)

# Generar token seguro
openssl rand -hex 32

# Aplicar cambios
docker-compose down -v  # ⚠️ Elimina datos
docker-compose up -d
```

### Monitorear Logs de Otro Servidor

```bash
# Editar docker-compose.yml
nano docker-compose.yml

# Línea del volumen del capturador:
volumes:
  - /ruta/a/tu/access.log:/var/log/apache2/access.log:ro

# Aplicar
docker-compose up -d --build capturador
```

---

## 💡 Recomendaciones

### Apache

```bash
# 1. Rotar logs regularmente para evitar archivos enormes
sudo nano /etc/logrotate.d/apache2

# Configuración recomendada:
# /var/log/apache2/*.log {
#     daily
#     rotate 14
#     compress
#     delaycompress
#     notifempty
#     create 640 root adm
# }

# 2. Monitorear tamaño de logs
du -h /var/log/apache2/access.log

# Si es > 1GB, rotar manualmente:
sudo logrotate -f /etc/logrotate.d/apache2

# 3. Habilitar mod_security (firewall de aplicaciones web)
sudo apt install libapache2-mod-security2 -y
sudo systemctl restart apache2

# 4. Configurar Apache para logs más detallados (opcional)
sudo nano /etc/apache2/apache2.conf
# Cambiar LogLevel de 'warn' a 'info'
```

### Seguridad

```bash
# 1. Cambiar credenciales por defecto
# Ver sección "Cambiar Credenciales"

# 2. Limitar acceso solo a localhost
# Editar docker-compose.yml:
ports:
  - "127.0.0.1:8086:8086"  # Solo localhost puede acceder

# 3. Hacer backup de InfluxDB
docker-compose exec influxdb influx backup /tmp/backup
docker-compose cp influxdb:/tmp/backup ./backups/backup_$(date +%Y%m%d)
```

### Rendimiento

```bash
# Limitar recursos en docker-compose.yml
nano docker-compose.yml

# Agregar bajo 'capturador':
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
```

### Monitoreo

```bash
# Ver métricas clave
curl -s http://localhost:9090/api/v1/query?query=logs_procesados_total | jq
curl -s http://localhost:9090/api/v1/query?query=log_anomalia_score | jq
curl -s http://localhost:9090/api/v1/query?query=log_anomalia_detectada | jq

# Alertar si MAE promedio > 0.03 (indica drift del modelo)
```

---

## 📁 Estructura del Proyecto

```
anomaly-detection-logs/
├── docker-compose.yml          # Orquestación
├── Dockerfile                  # Imagen capturador
├── prometheus.yml              # Config Prometheus
├── capturador.py              # Detección ML
├── requirements.txt           # Dependencias
├── modelo_logs_1.h5           # Modelo entrenado
├── scaler_logs_1.joblib       # Scaler
├── encoders_logs_1.joblib     # Encoders
├── MODELO_LOGS2.py            # Entrenamiento
└── LOGS_RANDOM.py             # Generador sintético
```

---

## 🔗 Enlaces Útiles

| Servicio | URL | Uso |
|----------|-----|-----|
| Grafana | http://localhost:3000 | Dashboards y alertas |
| Prometheus | http://localhost:9090 | Consultar métricas |
| InfluxDB | http://localhost:8086 | Ver datos históricos |
| Métricas | http://localhost:8000/metrics | Prometheus metrics |

---

## 👤 Autor

**KENET**  
Residencias Profesionales - Sistema de Gobierno Digital  

---

## 📄 Licencia

MIT License - Ver [LICENSE](LICENSE)

---

<div align="center">

**Quick Start**

```bash
# 1. Instalar Apache
sudo apt update && sudo apt install apache2 -y
sudo systemctl start apache2

# 2. Generar tráfico inicial
curl http://localhost/

# 3. Desplegar sistema
git clone https://github.com/tu-usuario/anomaly-detection-logs.git
cd anomaly-detection-logs
docker-compose up -d --build

# 4. Esperar 30 segundos
sleep 30

# 5. Verificar
curl http://localhost:8000/metrics
```

**Generar Tráfico Real**

```bash
# Tráfico normal
for i in {1..30}; do curl http://localhost/ > /dev/null 2>&1; sleep 0.5; done

# Tráfico anómalo
curl http://localhost/admin.php
curl http://localhost/.env
curl -A "sqlmap/1.0" http://localhost/
```

**Ver Resultados en Grafana:** http://localhost:3000

---

</div>
