import os
import subprocess
import re
import socket
import urllib.request
import json
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

socket.setdefaulttimeout(1.0)
console = Console()

# --- REGLAS ESTRICTAS DE PUERTOS (Basado en feedback del Core Team) ---
# Puertos que DEBEN estar expuestos al mundo
PUBLIC_PORTS = {
    '30333': 'P2P Network',
    '30334': 'P2P Network (Alt)',
    '443': 'Telemetría (HTTPS)'
}

# Puertos que NUNCA deben estar expuestos a IPs públicas
LOCAL_ONLY_PORTS = {
    '9944': 'RPC WebSockets',
    '9933': 'RPC HTTP',
    '9615': 'Prometheus Metrics'
}

SENSITIVE_DIRS = ['/etc/', '.ssh', '.bash', '/var/log/']
LEGITIMATE_DB_PATH = '.local/share/zkv-relay'

ip_cache = {}

def is_local_ip(ip):
    """Verifica si la IP pertenece a una red local o privada."""
    return ip.startswith('127.') or ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.')

def mask_ip(ip):
    """Oculta los últimos dos octetos de la IP pública por seguridad."""
    if is_local_ip(ip):
        return ip # No hace falta enmascarar IPs locales
    parts = ip.split('.')
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.***.***"
    return ip

def geolocate_ip(ip):
    if ip in ip_cache:
        return ip_cache[ip]
    
    if is_local_ip(ip):
        return "[dim]Localhost / LAN[/dim]", "Localhost / LAN"

    info_rich = "Desconocido"
    info_plain = "Desconocido"
    
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,countryCode,isp,org"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=1.5) as response:
            data = json.loads(response.read().decode())
            if data.get('status') == 'success':
                org = data.get('org', data.get('isp', 'ISP Desconocido'))
                country = data.get('countryCode', '??')
                org_short = org[:20] + ".." if len(org) > 20 else org
                info_rich = f"{org_short} [{country}]"
                info_plain = f"{org} [{country}]"
    except Exception:
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            info_rich = f"Host: {hostname[:20]}"
            info_plain = f"Host: {hostname}"
        except Exception:
            info_rich = "ISP Oculto/Timeout"
            info_plain = "ISP Oculto/Timeout"

    time.sleep(0.3)
    ip_cache[ip] = (info_rich, info_plain)
    return info_rich, info_plain

def get_suspicious_files(pid):
    try:
        result = subprocess.run(['sudo', 'lsof', '-p', str(pid), '-Fn'], capture_output=True, text=True)
        files = result.stdout.splitlines()
        suspicious = []
        for f in files:
            if f.startswith('n/'):
                filepath = f[1:]
                if any(sens in filepath for sens in SENSITIVE_DIRS) and LEGITIMATE_DB_PATH not in filepath:
                    suspicious.append(filepath)
        return suspicious[:2]
    except Exception:
        return []

def write_to_log(log_data):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("security_audit.log", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {log_data}\n")

def run_security_auditor(override_env="local", override_lang="en"):
    console.print("\n[bold cyan]🛡️ Iniciando Auditoría DeepSec (ZKV) - Control de Exposición...[/bold cyan]")
    
    with open("security_audit.log", "a", encoding="utf-8") as f:
        f.write(f"\n{'='*50}\nNUEVO ESCANEO OPSEC: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*50}\n")
    
    try:
        cmd = ['sudo', 'ss', '-tpn4', 'state', 'established']
        result = subprocess.run(cmd, capture_output=True, text=True)
        lines = result.stdout.splitlines()

        table = Table(title="[bold]Reporte de Postura de Seguridad y Amenazas[/bold]", border_style="cyan")
        table.add_column("Estado", justify="center", style="bold")
        table.add_column("IP Remota (Masked)", style="white")
        table.add_column("Rastreo (ISP/País)", style="magenta")
        table.add_column("Puerto", justify="center")
        table.add_column("Diagnóstico de Firewall", style="dim")

        found_connections = False
        console.print("[dim]Evaluando reglas de firewall y exposición de red...[/dim]\n")

        for line in lines[1:]: 
            if 'zkv-relay' not in line: continue
            
            found_connections = True
            parts = line.split()
            
            proc_idx = next((i for i, p in enumerate(parts) if 'zkv-relay' in p), -1)
            if proc_idx < 2: continue
                
            remote_address = parts[proc_idx - 1]
            local_address = parts[proc_idx - 2]
            
            try:
                remote_ip, remote_port = remote_address.rsplit(':', 1)
                local_ip, local_port = local_address.rsplit(':', 1)
            except ValueError: continue

            pid_match = re.search(r'pid=(\d+)', parts[proc_idx])
            pid = pid_match.group(1) if pid_match else None

            masked_ip = mask_ip(remote_ip)
            console.print(f" 📡 [cyan]Auditando IP:[/cyan] {masked_ip:<15} ... ", end="")
            isp_info_rich, isp_info_plain = geolocate_ip(remote_ip)
            console.print(f"[magenta]{isp_info_rich}[/magenta]")

            active_port = local_port if local_port in PUBLIC_PORTS or local_port in LOCAL_ONLY_PORTS else remote_port
            is_dynamic_p2p = active_port.isdigit() and 30300 <= int(active_port) <= 30999
            
            # --- EVALUACIÓN DE EXPOSICIÓN (El feedback del equipo) ---
            acceso_rich = "[green]Seguro[/green]"
            acceso_plain = "Seguro"

            if active_port in LOCAL_ONLY_PORTS:
                if is_local_ip(remote_ip):
                    tipo_rich = f"[blue]OK LOCAL ({LOCAL_ONLY_PORTS[active_port]})[/blue]"
                    tipo_plain = f"OK LOCAL ({LOCAL_ONLY_PORTS[active_port]})"
                    acceso_rich += " [dim](Uso interno correcto)[/dim]"
                    acceso_plain += " (Uso interno correcto)"
                else:
                    # ¡ALERTA! Un puerto privado está siendo accedido por una IP pública
                    tipo_rich = "[bold red]🚨 EXPOSICIÓN CRÍTICA[/bold red]"
                    tipo_plain = "EXPOSICION CRITICA"
                    acceso_rich = f"[bold red]Puerto {LOCAL_ONLY_PORTS[active_port]} expuesto públicamente![/bold red]"
                    acceso_plain = f"PUERTO {LOCAL_ONLY_PORTS[active_port]} EXPUESTO PUBLICAMENTE"
            elif active_port in PUBLIC_PORTS:
                tipo_rich = f"[green]OK PÚBLICO ({PUBLIC_PORTS[active_port]})[/green]"
                tipo_plain = f"OK PUBLICO ({PUBLIC_PORTS[active_port]})"
            elif is_dynamic_p2p:
                tipo_rich = "[green]OK (P2P Secundario)[/green]"
                tipo_plain = "OK (P2P Secundario)"
            else:
                tipo_rich = "[bold yellow]⚠️ PUERTO ATÍPICO[/bold yellow]"
                tipo_plain = "PUERTO ATIPICO"

            display_port = active_port

            # --- ANÁLISIS DE SISTEMA DE ARCHIVOS ---
            if pid:
                suspicious_files = get_suspicious_files(pid)
                if suspicious_files:
                    tipo_rich = "[bold red]🚨 INTROMISIÓN[/bold red]"
                    tipo_plain = "INTROMISION"
                    acceso_rich = f"[bold red]Tocando arch: {suspicious_files[0]}[/bold red]"
                    acceso_plain = f"TOCANDO ARCHIVO: {suspicious_files[0]}"

            table.add_row(tipo_rich, masked_ip, isp_info_rich, display_port, acceso_rich)
            log_line = f"IP: {remote_ip:<15} | Pto: {display_port:<5} | Est: {tipo_plain:<20} | ISP: {isp_info_plain:<30} | Diag: {acceso_plain}"
            write_to_log(log_line)

        if not found_connections:
            console.print(Panel("[yellow]No se detectaron conexiones activas para 'zkv-relay'.[/yellow]", border_style="yellow"))
        else:
            console.print("\n")
            console.print(table)
            console.print("\n[dim]💡 Tip: Los puertos RPC (9933/9944) y Metrics (9615) deben decir 'OK LOCAL'.\n    Si ves 'EXPOSICIÓN CRÍTICA', ajusta las reglas de tu firewall de inmediato.[/dim]\n")

    except KeyboardInterrupt:
        console.print("\n[yellow]Auditoría cancelada.[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")

    input("\nPresiona Enter para volver al menú...")

if __name__ == "__main__":
    run_security_auditor()
