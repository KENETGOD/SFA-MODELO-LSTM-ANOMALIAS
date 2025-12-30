# 📖 Guía Manual: Creación de Paneles en Grafana

## Panel 1: 🚨 Estado de Anomalía (Stat)

**Tipo:** Stat Panel  
**Data Source:** Prometheus

### Query:

```promql
log_anomalia_detectada
```

### Configuración:

- **Visualization:** Stat
- **Color Mode:** Background
- **Graph Mode:** Area
- **Thresholds:**
    - Base: Green (0)
    - Anomaly: Red (1)

---

## Panel 2: 📊 Score de Anomalía Actual (Stat)

**Tipo:** Stat Panel  
**Data Source:** Prometheus

### Query:

```promql
log_anomalia_score
```

### Configuración:

- **Visualization:** Stat
- **Decimals:** 4
- **Thresholds:**
    - Green: 0
    - Yellow: 0.1
    - Red: 0.15 (tu umbral)

---

## Panel 3: 📝 Total de Logs Procesados (Stat)

**Tipo:** Stat Panel  
**Data Source:** Prometheus

### Query:

```promql
logs_procesados_total
```

### Configuración:

- **Visualization:** Stat
- **Color Mode:** Value
- **Graph Mode:** Area

---

## Panel 4: 📈 Evolución del Score de Anomalía (Time Series)

**Tipo:** Time series  
**Data Source:** Prometheus

### Query:

```promql
log_anomalia_score
```

### Configuración:

- **Line Interpolation:** Smooth
- **Line Width:** 2
- **Fill Opacity:** 20
- **Show Points:** Auto
- **Threshold:** Line at 0.15 (red)
- **Legend:** Show min, max, mean

---

## Panel 5: 🔴 Detección de Anomalías en Tiempo Real (Time Series)

**Tipo:** Time series  
**Data Source:** Prometheus

### Query:

```promql
log_anomalia_detectada
```

### Configuración:

- **Line Interpolation:** Step After
- **Fill Opacity:** 50
- **Value Mappings:**
    - 0 → "Normal" (Green)
    - 1 → "Anomalía" (Red)

---

## Panel 6: ⚡ Tasa de Procesamiento (Time Series)

**Tipo:** Time series  
**Data Source:** Prometheus

### Query:

```promql
rate(logs_procesados_total[1m])
```

### Configuración:

- **Draw Style:** Bars
- **Fill Opacity:** 100
- **Legend:** Show sum

---

## Panel 7: 📊 Score de Anomalía desde InfluxDB (Time Series)

**Tipo:** Time series  
**Data Source:** InfluxDB

### Flux Query:

```flux
from(bucket: "network_traffic")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "web_traffic")
  |> filter(fn: (r) => r["_field"] == "score_anomalia")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")
```

### Configuración:

- **Line Interpolation:** Smooth
- **Fill Opacity:** 10
- **Legend:** Show mean, max

---

## Panel 8: 📋 Tabla de Logs Recientes (Table)

**Tipo:** Table  
**Data Source:** InfluxDB

### Flux Query:

```flux
from(bucket: "network_traffic")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "web_traffic")
  |> filter(fn: (r) => r["_field"] == "score_anomalia" or 
                       r["_field"] == "is_anomaly" or 
                       r["_field"] == "response_size")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> keep(columns: ["_time", "ip", "method", "status", "url", 
                    "score_anomalia", "is_anomaly", "response_size"])
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: 100)
```

### Configuraciones Especiales:

**Columna is_anomaly:**

- Cell Options: Color Background
- Value Mappings:
    - 0 → "✓ Normal" (Green)
    - 1 → "⚠ Anomalía" (Red)

**Columna score_anomalia:**

- Cell Options: Color Background
- Thresholds:
    - Green: < 0.1
    - Yellow: 0.1 - 0.15
    - Red: > 0.15

---

## Panel 9: 🌐 Top 10 IPs con Anomalías (Pie Chart)

**Tipo:** Pie chart  
**Data Source:** InfluxDB

### Flux Query:

```flux
from(bucket: "network_traffic")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "web_traffic")
  |> filter(fn: (r) => r["_field"] == "is_anomaly")
  |> group(columns: ["ip"])
  |> sum()
  |> group()
  |> sort(columns: ["_value"], desc: true)
  |> limit(n: 10)
```

### Configuración:

- **Legend:** Table with values
- **Pie Type:** Pie (or Donut)

---

## Panel 10: 🔧 Anomalías por Método HTTP (Time Series)

**Tipo:** Time series  
**Data Source:** InfluxDB

### Flux Query:

```flux
from(bucket: "network_traffic")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "web_traffic")
  |> filter(fn: (r) => r["_field"] == "is_anomaly")
  |> group(columns: ["method"])
  |> aggregateWindow(every: v.windowPeriod, fn: sum, createEmpty: false)
  |> yield(name: "sum")
```

### Configuración:

- **Draw Style:** Bars
- **Stacking:** Normal
- **Legend:** Show sum by method

---

# 🎨 Tips de Personalización

## Colores Consistentes

```
Verde:  #73BF69 (Normal)
Amarillo: #FADE2A (Warning)
Rojo:   #F2495C (Anomalía)
Azul:   #5794F2 (Info)
```

## Refresh Rate

- Dashboard Settings → Time Options → Refresh: **5s**
- Range: **Last 1 hour** (ajustar según necesidad)

## Organización

- Row 1: Métricas instantáneas (Stats)
- Row 2-3: Gráficas temporales
- Row 4: Tablas detalladas
- Row 5: Análisis agregados

# 🔔 Configuración de Alertas en Grafana

## Alerta 1: Detección de Anomalía

### Paso 1: Crear Alert Rule

1. Ve al panel "🚨 Estado de Anomalía"
2. Click en el título del panel → **Edit**
3. Tab **Alert** → **Create alert rule from this panel**

### Configuración:

```yaml
Rule name: Anomalía Detectada en Logs
Evaluate every: 10s
For: 30s  # Esperar 30s antes de alertar

# Condición
WHEN: log_anomalia_detectada
IS ABOVE: 0.5  # Detecta cuando pasa de 0 a 1

# Labels
severity: critical
team: security
```

### Mensaje de Alerta:

```
🚨 ANOMALÍA DETECTADA
Score: {{ $values.log_anomalia_score }}
Revisa el dashboard inmediatamente
```

---

## Alerta 2: Score de Anomalía Alto

### Configuración:

```yaml
Rule name: Score de Anomalía Elevado
Evaluate every: 30s
For: 1m

# Condición
WHEN: log_anomalia_score
IS ABOVE: 0.12  # Umbral preventivo (antes del 0.15)

# Labels
severity: warning
team: operations
```

### Mensaje:

```
⚠️ Score de Anomalía Elevado
Valor actual: {{ $values.log_anomalia_score }}
Umbral crítico: 0.15
```

---

## Alerta 3: Procesamiento Detenido

### Configuración:

```yaml
Rule name: Sistema de Detección Detenido
Evaluate every: 1m
For: 2m

# Condición
WHEN: increase(logs_procesados_total[2m])
IS BELOW: 1  # No ha procesado logs en 2 minutos

# Labels
severity: critical
team: infrastructure
```

---

## Canales de Notificación

### Email

1. **Alerting** → **Contact points** → **New contact point**
2. **Name:** Email Team
3. **Integration:** Email
4. **Addresses:** tu-email@example.com

### Slack (Opcional)

```yaml
Name: Slack Security
Integration: Slack
Webhook URL: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
Username: Grafana Alerts
```

### Discord (Opcional)

```yaml
Name: Discord Alerts
Integration: Discord
Webhook URL: https://discord.com/api/webhooks/YOUR_WEBHOOK
```

---

## Notification Policy

1. **Alerting** → **Notification policies**
2. **Default policy:**
    - **Contact point:** Email Team
    - **Group by:** alertname, severity
    - **Group wait:** 30s
    - **Group interval:** 5m
    - **Repeat interval:** 4h

---

## Test de Alertas

### Generar Anomalía Manual:

```bash
# Generar tráfico anómalo (múltiples requests rápidos)
for i in {1..100}; do
  curl -X POST http://localhost/anomalous-endpoint-$i
done
```

### Verificar:

1. Dashboard debe mostrar score > 0.15
2. Panel "Estado de Anomalía" debe ponerse ROJO
3. Alerta debe dispararse en 30s
4. Email/Slack debe recibirse