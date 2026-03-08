import json
import yaml
import os
import time
from substrateinterface import SubstrateInterface

TXT = {
    "en": {
        "title": " 🏛️  zkVerify GOVERNANCE AUDITOR (Uruguay Tool)",
        "conn": "📡 Connecting to environment:",
        "scanning": "🔍 Scanning zkVerify OpenGov...",
        "no_refs": "❌ No active referenda found.",
        "found": "\nFound {count} ongoing referenda:",
        "prompt_id": "\n👉 Select referendum ID to audit (or 'q' to quit): ",
        "tally_title": "🗳️  VOTING STATUS (REF #{id})",
        "ayes": "   ✅ Ayes:",
        "nays": "   ❌ Nays:",
        "support": "   📊 Total Support:",
        "decoding": "\n🕵️‍♂️ Decoding technical proposal...",
        "call_content": "\n📜 CALL CONTENT:",
        "no_preimage": "\n⚠️ Preimage not found. It might be an 'Inline' proposal or expired.",
        "err_node": "❌ Connection error:",
        "invalid": "❌ Invalid ID or input."
    },
    "es": {
        "title": " 🏛️  AUDITOR DE GOBERNANZA (Uruguay Command Center)",
        "conn": "📡 Conectando al entorno:",
        "scanning": "🔍 Escaneando la Gobernanza de zkVerify...",
        "no_refs": "❌ No se encontraron referéndums activos.",
        "found": "\nSe encontraron {count} referéndums en curso:",
        "prompt_id": "\n👉 Seleccioná el ID del referéndum (o 'q' para salir): ",
        "tally_title": "🗳️  ESTADO DE LA VOTACIÓN (REF #{id})",
        "ayes": "   ✅ Ayes:",
        "nays": "   ❌ Nays:",
        "support": "   📊 Soporte Total:",
        "decoding": "\n🕵️‍♂️ Decodificando propuesta técnica...",
        "call_content": "\n📜 CONTENIDO DE LA LLAMADA:",
        "no_preimage": "\n⚠️ No se encontró la Preimage. Puede ser una propuesta 'Inline' o expirada.",
        "err_node": "❌ Error de conexión:",
        "invalid": "❌ ID o entrada no válida."
    }
}

def run_gov_auditor(override_env=None, override_lang=None):
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            env = override_env if override_env else config['network']['env']
            node_url = config['network']['endpoints'][env]
            lang = override_lang if override_lang else config.get('preferences', {}).get('language', 'en')
    except Exception as e:
        print(f"❌ Error YAML: {e}"); return

    t = TXT[lang] if lang in TXT else TXT["en"]
    print("\n" + "="*55 + f"\n {t['title']}\n" + "="*55)
    
    try:
        substrate = SubstrateInterface(url=node_url)
    except Exception as e:
        print(f"{t['err_node']} {e}"); return

    print(t["scanning"])
    count = substrate.query('Referenda', 'ReferendumCount').value
    active_refs = []
    
    # Escaneo de los últimos 50 registros
    for i in range(max(0, count - 50), count):
        info = substrate.query('Referenda', 'ReferendumInfoFor', [i]).value
        if info and 'Ongoing' in info:
            active_refs.append({
                'id': i,
                'track': info['Ongoing']['track'],
                'proposal': info['Ongoing']['proposal'],
                'tally': info['Ongoing']['tally']
            })

    if not active_refs:
        print(t["no_refs"]); time.sleep(2); return

    print(t["found"].format(count=len(active_refs)))
    for r in active_refs:
        print(f"  [{r['id']}] Track: {r['track']}")

    choice = input(t["prompt_id"]).strip().lower()
    if choice == 'q': return

    try:
        selected = next((r for r in active_refs if str(r['id']) == choice), None)
        if selected:
            tally = selected['tally']
            ayes = int(tally['ayes']) / 10**18
            nays = int(tally['nays']) / 10**18
            support = int(tally['support']) / 10**18
            
            print("\n" + "-"*40)
            print(t["tally_title"].format(id=choice))
            print("-"*40)
            print(f"{t['ayes']:<20} {ayes:,.2f} VFY")
            print(f"{t['nays']:<20} {nays:,.2f} VFY")
            print(f"{t['support']:<20} {support:,.2f} VFY")
            print("-"*40)

            print(t["decoding"])
            
            # Manejo de Preimage (Lookup vs Inline)
            proposal = selected['proposal']
            preimage_data = None
            
            if 'Lookup' in proposal:
                p_hash = proposal['Lookup']['hash']
                p_len = proposal['Lookup']['len']
                preimage_data = substrate.query('Preimage', 'PreimageFor', [[p_hash, p_len]])
            
            if preimage_data and preimage_data.value:
                call = substrate.decode_scale('Call', preimage_data.value)
                print(t["call_content"])
                print(json.dumps(call, indent=4, default=str))
            else:
                print(t["no_preimage"])
        else:
            print(t["invalid"])
    except Exception as e:
        print(f"❌ Error: {e}")

    input("\nPress Enter to return...")

if __name__ == "__main__":
    run_gov_auditor()
