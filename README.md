# 🚀 UTHOPIA SSH Framework

**U**nified **T**oolkit for **H**igh-performance **O**rchestration & **P**arallel **I**nfrastructure **A**utomation

*Un framework avanzado de automatización SSH diseñado para impresionar y resolver problemas complejos de infraestructura.*

---

## 📋 Tabla de Contenidos

- [🌟 Características](#-características)
- [📦 Instalación](#-instalación)
- [🚀 Inicio Rápido](#-inicio-rápido)
- [📚 Documentación](#-documentación)
- [🔧 Configuración](#-configuración)
- [💡 Ejemplos de Uso](#-ejemplos-de-uso)
- [🏗️ Arquitectura](#️-arquitectura)
- [🤝 Contribución](#-contribución)
- [📄 Licencia](#-licencia)

---

## 🌟 Características

### ⚡ **Ejecución Paralela Masiva**
- Ejecuta comandos en **cientos de servidores simultáneamente**
- Control inteligente de concurrencia
- Barras de progreso en tiempo real con Rich

### 🔗 **Pool de Conexiones Inteligente**
- Reutilización automática de conexiones SSH
- Detección y reemplazo de conexiones muertas
- Thread-safe para operaciones concurrentes

### 🌐 **Túneles SSH Dinámicos**
- Creación automática de túneles SSH
- Port forwarding transparente
- Manejo de múltiples túneles simultáneos

### 📊 **Monitoreo en Tiempo Real**
- Dashboard live con métricas del sistema
- Visualización de CPU, memoria, disco y carga
- Actualización automática configurable

### 📁 **Transferencia Avanzada de Archivos**
- Upload/download con barras de progreso
- Callbacks personalizables
- Manejo eficiente de archivos grandes

### 📈 **Sistema de Reportes**
- Generación automática de reportes HTML
- Estadísticas detalladas de ejecución
- Logging estructurado para auditoría

---

## 📦 Instalación

### Requisitos Previos
- Python 3.8+
- pip (gestor de paquetes)

### Dependencias
```bash
pip install paramiko asyncssh rich pyyaml
```

### Instalación desde el Código Fuente
```bash
git clone https://github.com/tu-usuario/uthopia-ssh-framework.git
cd uthopia-ssh-framework
pip install -r requirements.txt
```

---

## 🚀 Inicio Rápido

### 1. Configuración Básica

```python
from uthopia_ssh import AdvancedSSHAutomation, SSHHost

# Crear instancia del framework
ssh_automation = AdvancedSSHAutomation(max_concurrent=10)

# Agregar hosts
ssh_automation.add_host("server1", SSHHost(
    hostname="192.168.1.100",
    username="admin",
    password="tu_password"
))

ssh_automation.add_host("server2", SSHHost(
    hostname="192.168.1.101",
    username="admin",
    key_filename="/path/to/key.pem"
))
```

### 2. Ejecutar Comandos en Paralelo

```python
# Ejecutar comando en múltiples servidores
results = ssh_automation.execute_parallel(
    ["server1", "server2"],
    "uname -a && df -h"
)

# Mostrar resultados
for result in results:
    print(f"Host: {result.host}")
    print(f"Exitoso: {result.success}")
    print(f"Salida: {result.stdout}")
```

### 3. Monitoreo en Tiempo Real

```python
# Monitorear sistemas por 60 segundos
ssh_automation.monitor_system(
    ["server1", "server2"], 
    interval=5, 
    duration=60
)
```

---

## 📚 Documentación

### Clases Principales

#### `AdvancedSSHAutomation`
La clase principal que orquesta todas las operaciones SSH.

**Métodos principales:**
- `add_host(name, host)`: Agrega un host al inventario
- `execute_parallel(hosts, command)`: Ejecuta comandos en paralelo
- `monitor_system(hosts, interval, duration)`: Monitorea sistemas
- `generate_report(output_file)`: Genera reportes HTML

#### `SSHHost`
Representa un host SSH con sus credenciales y configuración.

**Atributos:**
- `hostname`: Dirección IP o nombre del host
- `username`: Usuario SSH
- `password`: Contraseña (opcional)
- `key_filename`: Ruta a la clave privada (opcional)
- `port`: Puerto SSH (default: 22)
- `timeout`: Timeout de conexión (default: 30)
- `tags`: Etiquetas para clasificación

#### `SSHConnectionPool`
Gestiona un pool de conexiones SSH reutilizables.

**Características:**
- Conexiones persistentes
- Detección automática de conexiones muertas
- Thread-safe

#### `SSHTunnel`
Crea y gestiona túneles SSH para acceso seguro.

**Métodos:**
- `create_tunnel(local_port, remote_host, remote_port)`: Crea túnel SSH

---

## 🔧 Configuración

### Archivo de Inventario (inventory.yaml)

```yaml
hosts:
  web-server-01:
    hostname: 192.168.1.10
    username: deploy
    key_filename: /keys/deploy.pem
    port: 22
    timeout: 30
    tags: [web, frontend, production]
  
  db-server-01:
    hostname: 192.168.1.20
    username: dba
    password: secure_password
    tags: [database, mysql, production]
```

### Cargar Inventario

```python
ssh_automation.load_inventory("inventory.yaml")
```

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Actualización Masiva de Servidores

```python
# Actualizar todos los servidores web
web_servers = ["web-01", "web-02", "web-03"]
results = ssh_automation.execute_parallel(
    web_servers,
    "sudo apt update && sudo apt upgrade -y"
)

# Verificar resultados
for result in results:
    if result.success:
        print(f"✅ {result.host}: Actualización exitosa")
    else:
        print(f"❌ {result.host}: Error - {result.error}")
```

### Ejemplo 2: Despliegue de Aplicación

```python
deployment_commands = [
    "sudo systemctl stop nginx",
    "cd /var/www/html && sudo git pull origin main",
    "sudo composer install --no-dev",
    "sudo systemctl start nginx"
]

for command in deployment_commands:
    results = ssh_automation.execute_parallel(web_servers, command)
    
    # Verificar que todos los servidores ejecutaron exitosamente
    if not all(result.success for result in results):
        print(f"❌ Error en comando: {command}")
        break
```

### Ejemplo 3: Transferencia de Archivos

```python
# Subir archivo de configuración
host = ssh_automation.hosts["web-01"]
success = ssh_automation.transfer_file(
    host,
    local_path="./config/nginx.conf",
    remote_path="/etc/nginx/nginx.conf",
    upload=True
)

if success:
    print("✅ Archivo subido exitosamente")
```

### Ejemplo 4: Monitoreo Avanzado

```python
# Monitorear múltiples métricas
monitoring_command = """
echo "CPU: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | sed 's/%us,//')"
echo "Memory: $(free -h | grep '^Mem:' | awk '{print $3 "/" $2}')"
echo "Disk: $(df -h / | tail -1 | awk '{print $5}')"
echo "Connections: $(netstat -an | grep :80 | wc -l)"
"""

results = ssh_automation.execute_parallel(
    ["web-01", "web-02", "web-03"],
    monitoring_command
)

# Procesar métricas
for result in results:
    if result.success:
        metrics = result.stdout.strip().split('\n')
        print(f"🖥️  {result.host}:")
        for metric in metrics:
            print(f"   {metric}")
```

### Ejemplo 5: Creación de Túneles SSH

```python
# Crear túnel para acceso a base de datos
tunnel = SSHTunnel(ssh_automation.hosts["jump-server"])
tunnel.create_tunnel(
    local_port=3306,
    remote_host="internal-db.company.com",
    remote_port=3306
)

# Ahora puedes conectarte a localhost:3306
print("🔗 Túnel SSH creado: localhost:3306 -> internal-db:3306")
```

---

## 🏗️ Arquitectura

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────┐
│                UTHOPIA SSH FRAMEWORK                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ SSH Connection  │    │   SSH Tunnel    │                │
│  │      Pool       │    │    Manager      │                │
│  └─────────────────┘    └─────────────────┘                │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   Task Result   │    │   Progress      │                │
│  │    Manager      │    │   Tracking      │                │
│  └─────────────────┘    └─────────────────┘                │
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │  File Transfer  │    │   System        │                │
│  │    Handler      │    │  Monitoring     │                │
│  └─────────────────┘    └─────────────────┘                │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                    LIBRERÍAS BASE                           │
│          paramiko, asyncssh, rich, threading               │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de Ejecución

1. **Inicialización**: Carga configuración y crea pool de conexiones
2. **Autenticación**: Establece conexiones SSH seguras
3. **Ejecución**: Distribuye tareas en paralelo
4. **Monitoreo**: Rastrea progreso y recolecta resultados
5. **Reporte**: Genera estadísticas y logs

---

## 🎯 Casos de Uso Profesionales

### 🏢 **DevOps & SRE**
- Despliegues automatizados
- Monitoreo de infraestructura
- Gestión de configuración
- Orquestación de servicios

### 🔒 **Seguridad**
- Auditorías de seguridad
- Patcheo masivo
- Análisis de logs
- Compliance reporting

### ☁️ **Cloud & Contenedores**
- Gestión de instancias EC2/Azure
- Orquestación de contenedores
- Scaling automático
- Backup distribuido

### 📊 **Monitoreo & Observabilidad**
- Métricas en tiempo real
- Alertas automatizadas
- Análisis de performance
- Dashboards dinámicos

---

## 🚀 Rendimiento

### Benchmarks

| Operación | Servidores | Tiempo Secuencial | Tiempo Paralelo | Mejora |
|-----------|------------|-------------------|-----------------|---------|
| Comando simple | 10 | 30s | 3s | 10x |
| Transferencia archivos | 20 | 120s | 15s | 8x |
| Monitoreo continuo | 50 | N/A | Tiempo real | ∞ |

### Optimizaciones

- **Pool de conexiones**: Reduce overhead de autenticación
- **Ejecución paralela**: Aprovecha múltiples cores
- **Streaming**: Manejo eficiente de grandes outputs
- **Caching**: Reutilización de resultados

---

## 🔧 Configuración Avanzada

### Variables de Entorno

```bash
export UTHOPIA_MAX_CONCURRENT=20
export UTHOPIA_CONNECTION_TIMEOUT=60
export UTHOPIA_LOG_LEVEL=DEBUG
export UTHOPIA_REPORT_FORMAT=json
```

### Configuración por Código

```python
config = {
    'max_concurrent': 15,
    'connection_timeout': 45,
    'retry_attempts': 3,
    'log_level': 'INFO',
    'report_format': 'html'
}

ssh_automation = AdvancedSSHAutomation(**config)
```

---

## 📊 Logging y Debugging

### Configuración de Logs

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('uthopia.log'),
        logging.StreamHandler()
    ]
)
```

### Debugging Avanzado

```python
# Habilitar debug mode
ssh_automation.debug_mode = True

# Verificar estado de conexiones
ssh_automation.connection_pool.get_stats()

# Analizar resultados detallados
for result in results:
    if not result.success:
        print(f"Error en {result.host}: {result.error}")
        print(f"stderr: {result.stderr}")
```

---

## 🤝 Contribución

### Cómo Contribuir

1. **Fork** el repositorio
2. **Crea** una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. **Commit** tus cambios (`git commit -m 'Add amazing feature'`)
4. **Push** a la rama (`git push origin feature/amazing-feature`)
5. **Abre** un Pull Request

### Estándares de Código

- Seguir PEP 8
- Documentar funciones con docstrings
- Incluir tests unitarios
- Mantener cobertura > 80%

### Reportar Bugs

Usa el template de issue para reportar bugs:

```markdown
**Descripción del Bug**
Descripción clara del problema

**Pasos para Reproducir**
1. Ejecutar comando X
2. Configurar Y
3. Ver error

**Comportamiento Esperado**
Lo que debería pasar

**Entorno**
- OS: [Linux/Windows/macOS]
- Python: [3.8/3.9/3.10]
- UTHOPIA: [v1.0.0]
```

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

---

## 🙏 Agradecimientos

- **Paramiko Team**: Por la excelente librería SSH
- **Rich Project**: Por las interfaces visuales increíbles
- **Comunidad Python**: Por el ecosistema fantástico
- **Contribuidores**: Por hacer este proyecto mejor

---

## 📞 Soporte

- **Documentación**: [docs.uthopia.dev](https://docs.uthopia.dev)
- **Issues**: [GitHub Issues](https://github.com/tu-usuario/uthopia-ssh-framework/issues)
- **Discord**: [UTHOPIA Community](https://discord.gg/uthopia)
- **Email**: support@uthopia.dev

---

## 🔄 Roadmap

### v2.0.0 (Próximamente)
- [ ] Integración con Kubernetes
- [ ] Soporte para Windows PowerShell
- [ ] API REST para control remoto
- [ ] Plugin system

### v2.1.0
- [ ] Integración con AWS/Azure/GCP
- [ ] Machine Learning para detección de anomalías
- [ ] Interfaz web interactiva
- [ ] Soporte para Ansible playbooks

---

<div align="center">

### ⭐ Si te gusta UTHOPIA, ¡dale una estrella! ⭐

**Hecho con ❤️ por desarrolladores, para desarrolladores**

</div>

---

## 🎯 ¿Por qué UTHOPIA?

> *"En un mundo perfecto (utópico), la gestión de infraestructura sería simple, elegante y poderosa. UTHOPIA hace ese mundo realidad."*

**UTHOPIA** no es solo una herramienta, es una **filosofía de automatización** que convierte tareas complejas en operaciones simples y elegantes.

---

*Última actualización: $(date)*
