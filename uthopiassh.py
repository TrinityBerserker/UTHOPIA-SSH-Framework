#!/usr/bin/env python3
"""
Framework Avanzado de Automatización SSH
Características:
- Pool de conexiones concurrentes
- Túneles SSH dinámicos
- Transferencia de archivos con progress
- Ejecución de comandos paralelos
- Monitoreo en tiempo real
- Gestión de inventario de servidores
- Logging avanzado
- Recuperación automática de fallos
"""

import asyncio
import asyncssh
import paramiko
import threading
import time
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
import socket
import queue
import sys
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
import yaml

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ssh_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SSHHost:
    """Definición de un host SSH"""
    hostname: str
    username: str
    password: Optional[str] = None
    key_filename: Optional[str] = None
    port: int = 22
    timeout: int = 30
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class TaskResult:
    """Resultado de una tarea SSH"""
    host: str
    command: str
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    success: bool
    error: Optional[str] = None

class SSHConnectionPool:
    """Pool de conexiones SSH reutilizables"""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.connections: Dict[str, paramiko.SSHClient] = {}
        self.lock = threading.Lock()
        
    def get_connection(self, host: SSHHost) -> paramiko.SSHClient:
        """Obtiene una conexión del pool o crea una nueva"""
        host_key = f"{host.username}@{host.hostname}:{host.port}"
        
        with self.lock:
            if host_key in self.connections:
                conn = self.connections[host_key]
                if conn.get_transport() and conn.get_transport().is_active():
                    return conn
                else:
                    # Conexión muerta, remover del pool
                    del self.connections[host_key]
            
            # Crear nueva conexión
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                if host.key_filename:
                    ssh.connect(
                        host.hostname,
                        port=host.port,
                        username=host.username,
                        key_filename=host.key_filename,
                        timeout=host.timeout
                    )
                else:
                    ssh.connect(
                        host.hostname,
                        port=host.port,
                        username=host.username,
                        password=host.password,
                        timeout=host.timeout
                    )
                
                self.connections[host_key] = ssh
                return ssh
                
            except Exception as e:
                logger.error(f"Error conectando a {host_key}: {e}")
                raise
    
    def close_all(self):
        """Cierra todas las conexiones del pool"""
        with self.lock:
            for conn in self.connections.values():
                try:
                    conn.close()
                except:
                    pass
            self.connections.clear()

class SSHTunnel:
    """Gestión de túneles SSH"""
    
    def __init__(self, host: SSHHost):
        self.host = host
        self.tunnels: Dict[str, threading.Thread] = {}
        
    def create_tunnel(self, local_port: int, remote_host: str, remote_port: int):
        """Crea un túnel SSH"""
        tunnel_key = f"{local_port}:{remote_host}:{remote_port}"
        
        def tunnel_worker():
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            try:
                ssh.connect(
                    self.host.hostname,
                    port=self.host.port,
                    username=self.host.username,
                    password=self.host.password,
                    key_filename=self.host.key_filename
                )
                
                transport = ssh.get_transport()
                local_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                local_socket.bind(('localhost', local_port))
                local_socket.listen(1)
                
                logger.info(f"Túnel SSH activo: localhost:{local_port} -> {remote_host}:{remote_port}")
                
                while True:
                    client_socket, addr = local_socket.accept()
                    channel = transport.open_channel(
                        'direct-tcpip',
                        (remote_host, remote_port),
                        addr
                    )
                    
                    threading.Thread(
                        target=self._handle_tunnel_data,
                        args=(client_socket, channel)
                    ).start()
                    
            except Exception as e:
                logger.error(f"Error en túnel SSH: {e}")
            finally:
                ssh.close()
        
        thread = threading.Thread(target=tunnel_worker, daemon=True)
        thread.start()
        self.tunnels[tunnel_key] = thread
        
    def _handle_tunnel_data(self, client_socket, channel):
        """Maneja el intercambio de datos del túnel"""
        def forward_data(source, destination):
            try:
                while True:
                    data = source.recv(4096)
                    if not data:
                        break
                    destination.send(data)
            except:
                pass
            finally:
                source.close()
                destination.close()
        
        threading.Thread(target=forward_data, args=(client_socket, channel)).start()
        threading.Thread(target=forward_data, args=(channel, client_socket)).start()

class AdvancedSSHAutomation:
    """Framework principal de automatización SSH"""
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.connection_pool = SSHConnectionPool(max_concurrent)
        self.console = Console()
        self.hosts: Dict[str, SSHHost] = {}
        self.results: List[TaskResult] = []
        
    def add_host(self, name: str, host: SSHHost):
        """Agrega un host al inventario"""
        self.hosts[name] = host
        
    def load_inventory(self, file_path: str):
        """Carga inventario desde archivo YAML"""
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
            
        for name, config in data.get('hosts', {}).items():
            host = SSHHost(**config)
            self.add_host(name, host)
            
    def execute_command(self, host: SSHHost, command: str) -> TaskResult:
        """Ejecuta un comando en un host específico"""
        start_time = time.time()
        
        try:
            ssh = self.connection_pool.get_connection(host)
            stdin, stdout, stderr = ssh.exec_command(command)
            
            stdout_data = stdout.read().decode('utf-8')
            stderr_data = stderr.read().decode('utf-8')
            exit_code = stdout.channel.recv_exit_status()
            
            execution_time = time.time() - start_time
            
            result = TaskResult(
                host=host.hostname,
                command=command,
                stdout=stdout_data,
                stderr=stderr_data,
                exit_code=exit_code,
                execution_time=execution_time,
                success=exit_code == 0
            )
            
            logger.info(f"Comando ejecutado en {host.hostname}: {command}")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            result = TaskResult(
                host=host.hostname,
                command=command,
                stdout="",
                stderr="",
                exit_code=-1,
                execution_time=execution_time,
                success=False,
                error=str(e)
            )
            logger.error(f"Error ejecutando comando en {host.hostname}: {e}")
            return result
    
    def execute_parallel(self, hosts: List[str], command: str, 
                        progress_callback: Optional[Callable] = None) -> List[TaskResult]:
        """Ejecuta comandos en paralelo en múltiples hosts"""
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Ejecutando comandos...", total=len(hosts))
            
            with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
                future_to_host = {
                    executor.submit(self.execute_command, self.hosts[host], command): host
                    for host in hosts if host in self.hosts
                }
                
                for future in as_completed(future_to_host):
                    host = future_to_host[future]
                    try:
                        result = future.result()
                        results.append(result)
                        
                        if progress_callback:
                            progress_callback(result)
                            
                    except Exception as e:
                        logger.error(f"Error procesando resultado de {host}: {e}")
                    
                    progress.update(task, advance=1)
        
        self.results.extend(results)
        return results
    
    def transfer_file(self, host: SSHHost, local_path: str, remote_path: str, 
                     upload: bool = True) -> bool:
        """Transfiere archivos con barra de progreso"""
        try:
            ssh = self.connection_pool.get_connection(host)
            sftp = ssh.open_sftp()
            
            if upload:
                file_size = Path(local_path).stat().st_size
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    console=self.console
                ) as progress:
                    
                    task = progress.add_task(f"Subiendo {local_path}...", total=file_size)
                    
                    def progress_callback(bytes_transferred, total_bytes):
                        progress.update(task, completed=bytes_transferred)
                    
                    sftp.put(local_path, remote_path, callback=progress_callback)
            else:
                sftp.get(remote_path, local_path)
            
            sftp.close()
            logger.info(f"Archivo transferido: {local_path} -> {remote_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error transfiriendo archivo: {e}")
            return False
    
    def monitor_system(self, hosts: List[str], interval: int = 5, duration: int = 60):
        """Monitorea sistemas en tiempo real"""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body")
        )
        
        def get_system_info():
            command = """
            echo "=== SYSTEM INFO ==="
            echo "CPU: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | sed 's/%us,//')"
            echo "Memory: $(free -h | grep '^Mem:' | awk '{print $3 "/" $2}')"
            echo "Disk: $(df -h / | tail -1 | awk '{print $5}')"
            echo "Load: $(uptime | awk -F'load average:' '{print $2}')"
            """
            return self.execute_parallel(hosts, command)
        
        with Live(layout, refresh_per_second=1, console=self.console) as live:
            start_time = time.time()
            
            while time.time() - start_time < duration:
                # Header
                layout["header"].update(
                    Panel(
                        f"[bold green]Monitoreo de Sistemas[/bold green] - "
                        f"Tiempo restante: {duration - int(time.time() - start_time)}s",
                        style="bold blue"
                    )
                )
                
                # Body con información del sistema
                results = get_system_info()
                
                table = Table(title="Estado de Servidores")
                table.add_column("Host", style="cyan")
                table.add_column("CPU", style="magenta")
                table.add_column("Memoria", style="green")
                table.add_column("Disco", style="yellow")
                table.add_column("Carga", style="red")
                
                for result in results:
                    if result.success:
                        lines = result.stdout.strip().split('\n')
                        cpu = lines[1].split(': ')[1] if len(lines) > 1 else "N/A"
                        mem = lines[2].split(': ')[1] if len(lines) > 2 else "N/A"
                        disk = lines[3].split(': ')[1] if len(lines) > 3 else "N/A"
                        load = lines[4].split(': ')[1] if len(lines) > 4 else "N/A"
                        
                        table.add_row(result.host, cpu, mem, disk, load)
                    else:
                        table.add_row(result.host, "[red]ERROR[/red]", "[red]ERROR[/red]", 
                                    "[red]ERROR[/red]", "[red]ERROR[/red]")
                
                layout["body"].update(table)
                time.sleep(interval)
    
    def generate_report(self, output_file: str = "ssh_report.html"):
        """Genera reporte HTML de las operaciones"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>SSH Automation Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .success {{ color: green; }}
                .error {{ color: red; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .stats {{ background-color: #e6f3ff; padding: 10px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <h1>SSH Automation Report</h1>
            <div class="stats">
                <h2>Estadísticas</h2>
                <p>Total de tareas: {len(self.results)}</p>
                <p>Exitosas: {sum(1 for r in self.results if r.success)}</p>
                <p>Fallidas: {sum(1 for r in self.results if not r.success)}</p>
            </div>
            
            <h2>Detalles de Ejecución</h2>
            <table>
                <tr>
                    <th>Host</th>
                    <th>Comando</th>
                    <th>Estado</th>
                    <th>Tiempo (s)</th>
                    <th>Salida</th>
                </tr>
        """
        
        for result in self.results:
            status_class = "success" if result.success else "error"
            status_text = "✓" if result.success else "✗"
            
            html_content += f"""
                <tr>
                    <td>{result.host}</td>
                    <td><code>{result.command}</code></td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{result.execution_time:.2f}</td>
                    <td><pre>{result.stdout[:200]}...</pre></td>
                </tr>
            """
        
        html_content += """
            </table>
        </body>
        </html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Reporte generado: {output_file}")
    
    def cleanup(self):
        """Limpia recursos"""
        self.connection_pool.close_all()

# Ejemplo de uso avanzado
def main():
    # Crear instancia del framework
    ssh_automation = AdvancedSSHAutomation(max_concurrent=5)
    
    # Agregar hosts
    ssh_automation.add_host("server1", SSHHost(
        hostname="192.168.1.100",
        username="admin",
        password="password123"
    ))
    
    ssh_automation.add_host("server2", SSHHost(
        hostname="192.168.1.101",
        username="admin",
        key_filename="/path/to/key.pem"
    ))
    
    try:
        # Ejecutar comandos en paralelo
        results = ssh_automation.execute_parallel(
            ["server1", "server2"],
            "uname -a && df -h && free -h"
        )
        
        # Mostrar resultados
        table = Table(title="Resultados de Ejecución")
        table.add_column("Host", style="cyan")
        table.add_column("Estado", style="green")
        table.add_column("Tiempo", style="yellow")
        
        for result in results:
            status = "✓" if result.success else "✗"
            table.add_row(result.host, status, f"{result.execution_time:.2f}s")
        
        ssh_automation.console.print(table)
        
        # Monitorear sistemas (descomenta para usar)
        # ssh_automation.monitor_system(["server1", "server2"], interval=3, duration=30)
        
        # Generar reporte
        ssh_automation.generate_report()
        
    finally:
        ssh_automation.cleanup()

if __name__ == "__main__":
    main()
