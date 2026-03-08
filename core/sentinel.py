import time
import yaml
import os
from substrateinterface import SubstrateInterface
from datetime import datetime

# --- DICCIONARIO BILINGÜE ---
TXT = {
    "en": {
        "title": " 🛡️  ADVANCED NODE SENTINEL - ZKVERIFY (Core Module)",
        "err_yaml": "❌ Error loading config.yaml:",
        "conn": "📡 Connecting to environment:",
        "rate": "⏱️  Refresh rate:",
        "sec": "seconds",
        "monitor": "👀 Monitoring Consensus, Peers, and Mempool... (Press Ctrl+C to return to Menu)\n",
        "err_node": "❌ Failed to connect to node at",
        "tip_rpc": "💡 Tip: Make sure your local node is running with --rpc-port 9944",
        "crit": "🚨 CRITICAL: Cannot connect to RPC. Service down?",
        "warn_peers": "Low peer count",
        "danger_stall": "Consensus stalled by",
        "blocks": "blocks",
        "stop": "\n\n🛑 Monitoring stopped. Returning to main menu..."
    },
    "es": {
        "title": " 🛡️  CENTINELA AVANZADO DE NODO - ZKVERIFY (Módulo Core)",
        "err_yaml": "❌ Error al cargar config.yaml:",
        "conn": "📡 Conectando al entorno:",
        "rate": "⏱️  Tasa de refresco:",
        "sec": "segundos",
        "monitor": "👀 Monitoreando Consenso, Peers y Mempool... (Presiona Ctrl+C para volver al Menú)\n",
        "err_node": "❌ Fallo al conectar con el nodo en",
        "tip_rpc": "💡 Tip: Asegurate de que tu nodo local esté corriendo con --rpc-port 9944",
        "crit": "🚨 CRÍTICO: No se puede conectar al RPC. ¿Servicio caído?",
        "warn_peers": "Pocos peers",
        "danger_stall": "Consenso frenado por",
        "blocks": "bloques",
        "stop": "\n\n🛑 Monitoreo detenido. Volviendo al menú principal..."
    }
}

def run_sentinel(override_env=None, override_lang=None):
    # 1. Cargar la configuración
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            env = override_env if override_env else config['network']['env']
            ws_url = config['network']['endpoints'][env]
            lang = override_lang if override_lang else config.get('preferences', {}).get('language', 'en')
            interval = config['modules']['sentinel'].get('check_interval_seconds', 10)
    except Exception as e:
        print(f"❌ Error YAML: {e}")
        return

    # Fallback por si ponen un idioma raro
    if lang not in TXT: lang = "en"
    t = TXT[lang]

    print("=========================================================")
    print(t["title"])
    print("=========================================================")
    print(f"{t['conn']} {env.upper()} ({ws_url})")
    print(f"{t['rate']} {interval} {t['sec']}")
    print(t["monitor"])

    try:
        substrate = SubstrateInterface(url=ws_url)
    except Exception as e:
        print(f"{t['err_node']} {ws_url}: {e}")
        print(t["tip_rpc"])
        time.sleep(2)
        return

    def get_advanced_health():
        try:
            health = substrate.rpc_request('system_health', [])
            peers = health['result']['peers']
            sync_state = substrate.rpc_request('system_syncState', [])
            current_block = sync_state['result']['currentBlock']
            finalized_hash = substrate.get_chain_finalised_head()
            finalized_block = substrate.get_block_number(finalized_hash)
            mempool = substrate.rpc_request('author_pendingExtrinsics', [])['result']
            return peers, current_block, finalized_block, len(mempool)
        except Exception:
            return None, None, None, None

    last_block = 0
    try:
        while True:
            now = datetime.now().strftime("%H:%M:%S")
            peers, current_block, finalized_block, pending_tx = get_advanced_health()

            if peers is None:
                print(f"[{now}] {t['crit']}")
            else:
                status = "🟢 OK"
                warnings = []
                if peers < 3:
                    status = "🟡 WARN"
                    warnings.append(f"{t['warn_peers']} ({peers})")
                
                block_diff = current_block - finalized_block
                if block_diff > 5:
                    status = "🔴 DANGER"
                    warnings.append(f"{t['danger_stall']} {block_diff} {t['blocks']}")

                if current_block != last_block or status != "🟢 OK":
                    msg = f"[{now}] {status} | Peers: {peers:02d} | Blk: {current_block} (Fin: {finalized_block}) | Mempool: {pending_tx} txs"
                    if warnings: msg += f" | ⚠️  {', '.join(warnings)}"
                    print(msg)
                    last_block = current_block

            time.sleep(interval)

    except KeyboardInterrupt:
        print(t["stop"])
        time.sleep(1)
        return

if __name__ == "__main__":
    run_sentinel()
