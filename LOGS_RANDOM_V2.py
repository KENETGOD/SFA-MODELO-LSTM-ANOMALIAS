import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# ==========================================
# CONFIGURACIÓN
# ==========================================
NUM_ROWS = 1000000  # Número de registros a generar
FILENAME = "logs_servidorRAN1.csv"

# ==========================================
# DEFINICIÓN DE DATOS (CONSTANTES)
# ==========================================

# 1. MÉTODOS HTTP
methods = [
    'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 
    'HEAD', 'OPTIONS', 'CONNECT', 'TRACE'
]

# 2. URLs Y ENDPOINTS
urls = [
    # Páginas principales y públicas
    '/login', '/logout', '/home', '/index', '/dashboard', '/profile', '/settings', 
    '/about', '/contact', '/register', '/signup', '/signin', '/reset-password', 
    '/forgot-password', '/verify-email', '/terms', '/privacy', '/faq', '/help',
    '/support', '/documentation', '/pricing', '/features', '/demo', '/trial',
    '/download', '/upload', '/search', '/browse', '/explore', '/discover',
    
    # APIs versión 1
    '/api/v1/users', '/api/v1/users/list', '/api/v1/users/{id}', '/api/v1/users/search',
    '/api/v1/users/create', '/api/v1/users/update', '/api/v1/users/delete',
    '/api/v1/auth', '/api/v1/auth/login', '/api/v1/auth/logout', '/api/v1/auth/refresh',
    '/api/v1/token', '/api/v1/token/verify', '/api/v1/token/revoke',
    '/api/v1/products', '/api/v1/products/{id}', '/api/v1/products/categories',
    '/api/v1/products/featured', '/api/v1/products/popular', '/api/v1/products/new',
    '/api/v1/orders', '/api/v1/orders/{id}', '/api/v1/orders/history', '/api/v1/orders/pending',
    '/api/v1/payments', '/api/v1/payments/process', '/api/v1/payments/history',
    '/api/v1/search', '/api/v1/search/advanced', '/api/v1/notifications',
    '/api/v1/messages', '/api/v1/messages/inbox', '/api/v1/messages/sent',
    '/api/v1/comments', '/api/v1/comments/{id}', '/api/v1/likes', '/api/v1/shares',
    '/api/v1/reports', '/api/v1/analytics', '/api/v1/statistics', '/api/v1/metrics',
    '/api/v1/settings', '/api/v1/preferences', '/api/v1/profile', '/api/v1/avatar',
    '/api/v1/upload', '/api/v1/download', '/api/v1/export', '/api/v1/import',
    
    # APIs versión 2
    '/api/v2/users', '/api/v2/users/batch', '/api/v2/users/roles', '/api/v2/users/permissions',
    '/api/v2/analytics', '/api/v2/analytics/dashboard', '/api/v2/analytics/reports',
    '/api/v2/metrics', '/api/v2/metrics/realtime', '/api/v2/metrics/historical',
    '/api/v2/logs', '/api/v2/logs/search', '/api/v2/logs/export',
    '/api/v2/health', '/api/v2/health/check', '/api/v2/status', '/api/v2/version',
    '/api/v2/config', '/api/v2/config/update', '/api/v2/upload', '/api/v2/download',
    '/api/v2/files', '/api/v2/files/{id}', '/api/v2/files/metadata',
    '/api/v2/webhooks', '/api/v2/webhooks/register', '/api/v2/webhooks/test',
    '/api/v2/integrations', '/api/v2/integrations/oauth', '/api/v2/integrations/callback',
    
    # APIs versión 3
    '/api/v3/graphql', '/api/v3/rest', '/api/v3/streaming', '/api/v3/realtime',
    '/api/v3/batch', '/api/v3/queue', '/api/v3/jobs', '/api/v3/tasks',
    
    # Archivos estáticos
    '/static/css/style.css', '/static/css/main.css', '/static/css/bootstrap.min.css',
    '/static/js/app.js', '/static/js/main.js', '/static/js/jquery.min.js',
    '/static/images/logo.png', '/static/images/hero.png', '/static/images/icon.ico',
    
    # Panel de administración
    '/admin', '/admin/login', '/admin/dashboard', '/admin/users',
    '/admin/logs', '/admin/settings', '/admin/reports', '/admin/analytics',
    
    # Webhooks y callbacks
    '/webhook/payment', '/webhook/notification', '/callback/oauth',
    
    # Rutas sospechosas y de ataques
    '/admin.php', '/administrator.php', '/wp-admin', '/wp-login.php',
    '/phpmyadmin', '/.env', '/.git/config', '/shell.php', '/config.php',
    '/etc/passwd', '/server-status', '/test.php'
]

# 3. VERSIONES HTTP
http_versions = [
    'HTTP/0.9', 'HTTP/1.0', 'HTTP/1.1', 'HTTP/2.0', 'HTTP/3.0', 'SPDY/3.1'
]

# 4. CÓDIGOS DE ESTADO
status_codes = [
    100, 101, 102, 
    200, 201, 202, 204, 206, 
    300, 301, 302, 304, 307, 308, 
    400, 401, 403, 404, 405, 408, 409, 410, 418, 429, 
    500, 501, 502, 503, 504
]

# 5. USER AGENTS
user_agents = [
    # Chrome
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    
    # Firefox
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0',
    
    # Safari
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    
    # Edge
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
    
    # Android
    'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36',
    
    # Bots - Google
    'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Googlebot/2.1 (+http://www.google.com/bot.html)',
    'Googlebot-Image/1.0',
    'Googlebot-News',
    'Googlebot-Video/1.0',

    # Bots - Bing & Yahoo
    'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)',
    'Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)',

    # Herramientas de desarrollo
    'curl/8.5.0',
    'PostmanRuntime/7.36.0',
    'python-requests/2.31.0',
    'Apache-HttpClient/4.5.14 (Java/11.0.20)'
]

# 6. VERSIONES TLS
tls_versions = [
    'SSLv2', 'SSLv3', 'TLSv1.0', 'TLSv1.1', 'TLSv1.2', 'TLSv1.3', 'DTLS 1.2', '-'
]

# 7. CIPHER SUITES
cipher_suites = [
    'TLS_AES_128_GCM_SHA256',
    'TLS_AES_256_GCM_SHA384',
    'TLS_CHACHA20_POLY1305_SHA256',
    'ECDHE-RSA-AES128-GCM-SHA256',
    'ECDHE-RSA-AES256-GCM-SHA384',
    'ECDHE-ECDSA-AES128-GCM-SHA256',
    'DHE-RSA-AES256-GCM-SHA384',
    'AES128-GCM-SHA256',
    'ECDHE-RSA-RC4-SHA', # Legacy
    'NULL-SHA256',       # Inseguro
    '-'
]

# 8. DIRECCIONES IP (GENERACIÓN)
private_ips_class_a = [f'10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}' for _ in range(100)]
private_ips_class_b = [f'172.{random.randint(16, 31)}.{random.randint(0, 255)}.{random.randint(1, 254)}' for _ in range(80)]
private_ips_class_c = [f'192.168.{random.randint(0, 255)}.{random.randint(1, 254)}' for _ in range(120)]
special_ips = ['127.0.0.1', '0.0.0.0', '169.254.1.1']
public_ips_na = [f'{random.randint(1, 126)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}' for _ in range(80)]
public_ips_eu = [f'{random.randint(128, 191)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}' for _ in range(60)]
public_ips_asia = [f'{random.randint(192, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}' for _ in range(60)]
known_service_ips = ['8.8.8.8', '1.1.1.1', '208.67.222.222', '104.16.0.0']

# Combinar todas las IPs
ips = (private_ips_class_a + private_ips_class_b + private_ips_class_c +
       special_ips + public_ips_na + public_ips_eu + public_ips_asia +
       known_service_ips)

# 9. REFERRERS
referers = [
    'https://www.google.com/', 'https://www.bing.com/', 'https://duckduckgo.com/',
    'https://www.facebook.com/', 'https://twitter.com/', 'https://www.linkedin.com/',
    'https://www.instagram.com/', 'https://www.reddit.com/', 'https://www.youtube.com/',
    'https://stackoverflow.com/', 'https://github.com/', 'https://news.ycombinator.com/',
    'https://medium.com/', 'direct', '-', 'internal'
]

# 10. FUENTES DE LOG
log_sources = [
    'nginx_access_log', 'nginx_error_log', 'apache_access_log', 'iis_access_log',
    'haproxy_log', 'aws_alb_log', 'cloudfront_log', 'cloudflare_log',
    'firewall_log', 'waf_log', 'fail2ban_log',
    'application_log', 'django_log', 'nodejs_log', 'auth_log', 'syslog',
    'mysql_slow_query_log', 'postgres_log', 'docker_log', 'kubernetes_log'
]

# ==========================================
# GENERAR DATOS
# ==========================================
data = []
base_time = datetime.now()

print(f"[+] Generando {NUM_ROWS} registros de logs simulados...")
print(f"[+] Datos expandidos con categorías masivas:")
print(f"    - Métodos HTTP: {len(methods)}")
print(f"    - URLs: {len(urls)}")
print(f"    - User Agents: {len(user_agents)}")
print(f"    - Versiones HTTP: {len(http_versions)}")
print(f"    - Códigos de estado: {len(status_codes)}")
print(f"    - Versiones TLS: {len(tls_versions)}")
print(f"    - Cipher Suites: {len(cipher_suites)}")
print(f"    - IPs disponibles: {len(ips)}")
print(f"    - Referers: {len(referers)}")
print(f"    - Fuentes de log: {len(log_sources)}")
print()

for i in range(NUM_ROWS):
    row = {
        'ip': random.choice(ips),
        'method': random.choice(methods),
        'url': random.choice(urls),
        'http_version': random.choice(http_versions),
        'status_code': random.choice(status_codes),
        'response_size': np.random.randint(100, 5000),  # Bytes
        'referer': random.choice(referers),
        'user_agent': random.choice(user_agents),
        'tls_version': random.choice(tls_versions),
        'cipher_suite': random.choice(cipher_suites),
        'log_source': random.choice(log_sources),
        'timestamp': base_time + timedelta(seconds=i*2)  # Incremento de 2 segundos
    }
    data.append(row)

    # Mostrar progreso cada 1000 registros
    if (i + 1) % 1000 == 0:
        print(f"[*] Progreso: {i + 1}/{NUM_ROWS} registros generados...")

# ==========================================
# CREAR DATAFRAME Y GUARDAR
# ==========================================
df = pd.DataFrame(data)
df.to_csv(FILENAME, index=False)

print()
print(f"[✓] Archivo '{FILENAME}' generado exitosamente.")
print(f"[✓] Total de registros: {len(df)}")
# Cálculo seguro del tamaño en memoria
mem_usage = df.memory_usage(deep=True).sum() / (1024 * 1024)
print(f"[✓] Tamaño del archivo en memoria: {mem_usage:.2f} MB")
print()
print("[-] Resumen estadístico:")
print(f"    - IPs únicas: {df['ip'].nunique()}")
print(f"    - URLs únicas: {df['url'].nunique()}")
print(f"    - User Agents únicos: {df['user_agent'].nunique()}")
print(f"    - Métodos HTTP únicos: {sorted(df['method'].unique())}")
print(f"    - Rango de códigos de estado: {df['status_code'].min()} - {df['status_code'].max()}")
print(f"    - Fuentes de log únicas: {df['log_source'].nunique()}")
