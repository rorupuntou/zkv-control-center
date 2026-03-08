import json
import pydoc
import yaml
import os
from substrateinterface import SubstrateInterface

TXT = {
    "en": {
        "title": " 🔍 zkVerify Block Master CLI (Core Module)",
        "conn": "📡 Connecting to environment:",
        "input_blk": "🔹 Enter block number (Enter for latest, 'q' to quit): ",
        "quit": "🛑 Returning to main menu...",
        "err_pruned": "❌ Error: Block is too old for your local node.\n💡 Tip: Your node is 'Pruned'. Use a Public Archive RPC.",
        "sel_title": "\n--- [1] SELECTION ---",
        "sel_1": "1. All Transactions",
        "sel_2": "2. System/Header only (First 2)",
        "sel_3": "3. Quick Count only",
        "choice": "Choice (1-3): ",
        "tot_txs": "✅ Total TXs in block",
        "fmt_title": "\n--- [2] DATA FORMAT ---",
        "fmt_1": "1. Full Decoded JSON (Human-readable)",
        "fmt_2": "2. Only TXIDs List",
        "fmt_3": "3. Raw Hex (SCALE encoded)",
        "ask_det": "\n📝 Include full params & signatures? (y/n): ",
        "vw_title": "\n--- [3] VIEW OPTIONS ---",
        "vw_1": "1. View Collapsed (Fast Preview)",
        "vw_2": "2. View Full (Separate Window/Pager)",
        "vw_choice": "Choice (1-2): ",
        "hidden": "[HIDDEN]",
        "err_exit": "\n👋 Emergency exit..."
    },
    "es": {
        "title": " 🔍 zkVerify Block Master CLI (Módulo Core)",
        "conn": "📡 Conectando al entorno:",
        "input_blk": "🔹 Ingresa el N° de bloque (Enter para el último, 'q' para salir): ",
        "quit": "🛑 Volviendo al menú principal...",
        "err_pruned": "❌ Error: El bloque es muy viejo.\n💡 Tip: Tu nodo está en modo 'Pruned'. Usá un RPC Público.",
        "sel_title": "\n--- [1] SELECCIÓN ---",
        "sel_1": "1. Todas las Transacciones",
        "sel_2": "2. Solo System/Header (Primeras 2)",
        "sel_3": "3. Solo Conteo Rápido",
        "choice": "Elige (1-3): ",
        "tot_txs": "✅ Total TXs en el bloque",
        "fmt_title": "\n--- [2] FORMATO DE DATOS ---",
        "fmt_1": "1. JSON Decodificado Completo (Legible)",
        "fmt_2": "2. Solo Lista de TXIDs",
        "fmt_3": "3. Hex Crudo (SCALE encoded)",
        "ask_det": "\n📝 ¿Incluir parámetros completos y firmas? (y/n): ",
        "vw_title": "\n--- [3] OPCIONES DE VISTA ---",
        "vw_1": "1. Vista Colapsada (Previa Rápida)",
        "vw_2": "2. Vista Completa (Paginador)",
        "vw_choice": "Elige (1-2): ",
        "hidden": "[OCULTO]",
        "err_exit": "\n👋 Saliendo de emergencia..."
    }
}

def clean_txid(txid):
    if not txid: return "0x"
    return f"0x{str(txid).replace('0x', '')}"

def format_output(data, hidden_text, collapse=True):
    if not collapse: return json.dumps(data, indent=4)
    formatted_data = json.loads(json.dumps(data))
    
    def truncate_recursive(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str) and v.startswith("0x") and len(v) > 66:
                    obj[k] = f"{v[:10]}...{v[-10:]} {hidden_text}"
                elif isinstance(v, (dict, list)):
                    truncate_recursive(v)
        elif isinstance(obj, list):
            for item in obj: truncate_recursive(item)

    truncate_recursive(formatted_data)
    return json.dumps(formatted_data, indent=4)

def run_block_master(override_env=None, override_lang=None):
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            env = override_env if override_env else config['network']['env']
            node_url = config['network']['endpoints'][env]
            lang = override_lang if override_lang else config.get('preferences', {}).get('language', 'en')
    except Exception as e:
        print(f"❌ Error YAML: {e}")
        return

    if lang not in TXT: lang = "en"
    t = TXT[lang]

    print("\n" + "="*55)
    print(t["title"])
    print("="*55)
    print(f"{t['conn']} {env.upper()} ({node_url})")
    
    try:
        substrate = SubstrateInterface(url=node_url)
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    def get_block_data(block_num=None):
        block_hash = substrate.get_block_hash(block_num) if block_num else substrate.get_chain_head()
        return substrate.get_block(block_hash=block_hash), block_hash

    while True:
        print("\n" + "-"*40)
        block_input = input(t["input_blk"]).strip()
        
        if block_input.lower() == 'q':
            print(t["quit"])
            break
            
        block_num = int(block_input) if block_input else None
        
        try:
            block, b_hash = get_block_data(block_num)
            header = block['header']
            extrinsics = block['extrinsics']
        except Exception as e:
            if "State already discarded" in str(e) or "4003" in str(e):
                print(t["err_pruned"])
            else:
                print(f"❌ Error: {e}")
            continue

        print(f"\n📦 Blk: {header['number']} | Hash: {b_hash[:16]}... | TXs: {len(extrinsics)}")
        
        print(t["sel_title"])
        print(t["sel_1"]); print(t["sel_2"]); print(t["sel_3"])
        opt = input(t["choice"])

        if opt == "3":
            print(f"\n{t['tot_txs']} {header['number']}: {len(extrinsics)}")
            continue
        
        print(t["fmt_title"])
        print(t["fmt_1"]); print(t["fmt_2"]); print(t["fmt_3"])
        data_type = input(t["choice"])

        include_details = "n"
        if data_type == "1":
            include_details = input(t["ask_det"]).lower()

        results = []
        for i, ext in enumerate(extrinsics):
            if opt == "2" and i >= 2: break
            val = getattr(ext, 'value', {})
            
            if data_type == "2":
                results.append(clean_txid(val.get('extrinsic_hash')))
            elif data_type == "3":
                results.append(ext.data.to_hex())
            else:
                is_signed = val.get('address') is not None
                tx = {
                    "index": i,
                    "txid": clean_txid(val.get('extrinsic_hash')),
                    "signer": val.get('address') if is_signed else "SYSTEM/INHERENT",
                    "module": ext.value['call']['call_module'],
                    "function": ext.value['call']['call_function']
                }
                if include_details == "y":
                    tx["params"] = val.get('call', {}).get('call_args', {})
                    tx["signature"] = val.get('signature')
                else:
                    tx["hex_preview"] = f"{ext.data.to_hex()[:40]}..."
                results.append(tx)

        output_obj = {
            "metadata": {"block_number": header['number'], "block_hash": b_hash},
            "results": results
        }

        print(t["vw_title"])
        print(t["vw_1"]); print(t["vw_2"])
        view_opt = input(t["vw_choice"])

        if view_opt == "1":
            print("\n" + format_output(output_obj, t["hidden"], collapse=True))
        else:
            pydoc.pager(format_output(output_obj, t["hidden"], collapse=False))

if __name__ == "__main__":
    try:
        run_block_master()
    except KeyboardInterrupt:
        print(TXT["en"]["err_exit"])
