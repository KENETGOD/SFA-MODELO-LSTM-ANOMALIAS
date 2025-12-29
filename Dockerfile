# Usa una imagen base de Python
FROM python:3.12-slim

# Variables de entorno
ENV PYTHONUNBUFFERED=1

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo de requerimientos
COPY requirements.txt .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de tu aplicación
COPY . .

# Verifica que los archivos del modelo existan
RUN echo "Verificando archivos del modelo..." && \
    ls -la modelo_logs_1.h5 scaler_logs_1.joblib encoders_logs_1.joblib || \
    (echo "ERROR: Faltan archivos del modelo!" && exit 1)

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/metrics || exit 1

# Comando para ejecutar la aplicación
CMD ["python", "-u", "capturador.py"]
