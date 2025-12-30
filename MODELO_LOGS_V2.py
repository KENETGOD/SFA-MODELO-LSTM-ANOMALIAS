import pandas as pd
import numpy as np
import joblib
import os
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN TENSORFLOW Y GPU ---
import tensorflow as tf

def configurar_gpu():
    """Configura TensorFlow para usar GPU si está disponible"""
    print("="*70)
    print("CONFIGURACIÓN DE ACELERACIÓN POR HARDWARE")
    print("="*70)
    
    print(f"TensorFlow versión: {tf.__version__}")
    print(f"Construido con CUDA: {tf.test.is_built_with_cuda()}")
    
    # Detectar GPUs
    gpus = tf.config.list_physical_devices('GPU')
    
    if gpus:
        try:
            # Configurar crecimiento de memoria
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
            
            print(f"✓ GPUs detectadas: {len(gpus)}")
            for i, gpu in enumerate(gpus):
                print(f"  GPU {i}: {gpu.name}")
            
            # Información adicional
            print(f"✓ Dispositivo de cómputo: GPU")
            print(f"✓ Mixed Precision: Disponible")
            
            # Habilitar Mixed Precision para mejor rendimiento
            # Descomenta si quieres usar precisión mixta (más rápido)
            # tf.keras.mixed_precision.set_global_policy('mixed_float16')
            # print("✓ Mixed Precision habilitada (float16)")
            
        except RuntimeError as e:
            print(f"✗ Error configurando GPU: {e}")
            print("  Entrenamiento continuará en CPU")
    else:
        print("✗ No se detectaron GPUs")
        print("  Causas posibles:")
        print("    1. TensorFlow versión CPU instalada")
        print("    2. Drivers NVIDIA no instalados/actualizados")
        print("    3. CUDA Toolkit no instalado")
        print("    4. cuDNN no instalado")
        print("  Entrenamiento continuará en CPU (será más lento)")
    
    print("="*70)
    print()

# Llamar configuración al inicio
configurar_gpu()

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, RepeatVector, TimeDistributed, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# --- CONFIGURACIÓN ---
DATA_FILE = 'logs_servidorRAN10.csv' 
MODEL_NAME = 'modelo_logs_3.h5'
SCALER_FILE = 'scaler_logs_3.joblib'
ENCODERS_FILE = 'encoders_logs_3.joblib'
TIMESTEPS = 10 

def cargar_y_preprocesar_datos(filepath):
    print(f"[*] Cargando datos desde {filepath}...")
    try:
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filepath.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath)
        else:
            print("[*] Extensión desconocida, intentando leer como CSV...")
            df = pd.read_csv(filepath)
            
    except Exception as e:
        print(f"[!] Error leyendo el archivo de datos: {e}")
        print("    Sugerencia: Si es un CSV, revisa el separador (coma vs punto y coma).")
        exit()

    # 1. Ordenar por tiempo
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])
        df = df.sort_values('timestamp')
        df = df.drop(columns=['timestamp'])
    
    # 2. Manejo de columnas categóricas
    categorical_cols = ['ip', 'method', 'url', 'http_version', 'referer', 
                        'user_agent', 'tls_version', 'cipher_suite', 'log_source']
    
    numerical_cols = ['status_code', 'response_size']

    encoders = {}
    
    print("[*] Codificando columnas categóricas...")
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].astype(str)
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col])
            encoders[col] = le

    # 3. Escalado
    print("[*] Escalando datos...")
    scaler = MinMaxScaler()
    
    feature_cols = [c for c in df.columns if c in categorical_cols or c in numerical_cols]
    
    if not feature_cols:
        print("[!] Error: No se encontraron columnas válidas para entrenar.")
        print(f"    Columnas disponibles en el archivo: {list(df.columns)}")
        exit()

    data_scaled = scaler.fit_transform(df[feature_cols])
    
    joblib.dump(scaler, SCALER_FILE)
    joblib.dump(encoders, ENCODERS_FILE)
    print(f"[*] Preprocesamiento guardado en '{SCALER_FILE}' y '{ENCODERS_FILE}'")
    
    return data_scaled, len(feature_cols)

def crear_secuencias(data, time_steps=10):
    print(f"[*] Creando secuencias con ventana de tiempo = {time_steps}...")
    sequences = []
    for i in range(len(data) - time_steps):
        sequences.append(data[i:(i + time_steps)])
    return np.array(sequences)

def construir_modelo(input_shape):
    print(f"[*] Construyendo modelo Stacked LSTM con input: {input_shape}...")
    
    # El modelo se construirá automáticamente en GPU si está disponible
    model = Sequential()
    
    # Encoder
    model.add(LSTM(128, activation='relu', input_shape=input_shape, return_sequences=True))
    model.add(Dropout(0.2))
    model.add(LSTM(64, activation='relu', return_sequences=False))
    model.add(Dropout(0.2))
    
    # Bridge
    model.add(RepeatVector(input_shape[0]))
    
    # Decoder
    model.add(LSTM(64, activation='relu', return_sequences=True))
    model.add(Dropout(0.2))
    model.add(LSTM(128, activation='relu', return_sequences=True))
    
    # Output
    model.add(TimeDistributed(Dense(input_shape[1])))
    
    model.compile(optimizer='adam', loss='mae')
    
    print(f"[*] Modelo creado con {model.count_params():,} parámetros entrenables")
    
    return model

def entrenar():
    if not os.path.exists(DATA_FILE):
        print(f"[!] No se encuentra el archivo '{DATA_FILE}'.")
        return

    data_scaled, num_features = cargar_y_preprocesar_datos(DATA_FILE)
    
    X = crear_secuencias(data_scaled, TIMESTEPS)
    
    if len(X) == 0:
        print("[!] No hay suficientes datos para crear secuencias. Necesitas más filas en tu CSV.")
        return

    X_train, X_test = train_test_split(X, test_size=0.2, random_state=42, shuffle=False)
    
    print(f"    -> Datos de entrenamiento: {X_train.shape}")
    print(f"    -> Datos de prueba: {X_test.shape}")

    model = construir_modelo((X_train.shape[1], X_train.shape[2]))
    
    early_stopping = EarlyStopping(monitor='val_loss', patience=5, mode='min', verbose=1)
    checkpoint = ModelCheckpoint(MODEL_NAME, save_best_only=True, monitor='val_loss', mode='min', verbose=1)

    print("\n" + "="*70)
    print("INICIANDO ENTRENAMIENTO")
    print("="*70)
    
    # Mostrar en qué dispositivo se está entrenando
    with tf.device('/GPU:0' if tf.config.list_physical_devices('GPU') else '/CPU:0'):
        history = model.fit(
            X_train, X_train,
            epochs=50,
            batch_size=32,
            validation_data=(X_test, X_test),
            callbacks=[early_stopping, checkpoint],
            verbose=1
        )

    print(f"\n[✓] Modelo guardado exitosamente como '{MODEL_NAME}'")
    
    # Graficar resultados
    try:
        plt.figure(figsize=(10, 6))
        plt.plot(history.history['loss'], label='Training Loss', linewidth=2)
        plt.plot(history.history['val_loss'], label='Validation Loss', linewidth=2)
        plt.xlabel('Época', fontsize=12)
        plt.ylabel('Pérdida (MAE)', fontsize=12)
        plt.title('Curva de Aprendizaje - Modelo LSTM', fontsize=14, fontweight='bold')
        plt.legend(fontsize=11)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('grafico_entrenamiento_3.png', dpi=150)
        print("[✓] Gráfico de entrenamiento guardado como 'grafico_entrenamiento_3.png'")
    except Exception as e:
        print(f"[!] No se pudo generar el gráfico: {e}")

if __name__ == '__main__':
    entrenar()
