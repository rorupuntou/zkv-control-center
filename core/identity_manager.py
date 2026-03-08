import yaml
import os
import getpass
import time
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

TXT = {
    "en": {
        "title": " 🆔 ON-CHAIN IDENTITY MANAGER - ZKVERIFY",
        "conn": "📡 Connecting to environment:",
        "sec_notice": "⚠️  SECURITY: Mnemonic is processed locally and NEVER transmitted.",
        "prompt_mne": "🔑 Enter mnemonic (leave empty to use config.yaml): ",
        "wallet_ok": "🔓 Wallet unlocked: ",
        "err_wallet": "❌ Failed to load wallet. Check your mnemonic.",
        "prompt_name": "\n📝 Enter desired Display Name (e.g. RORU_NODE): ",
        "prep": "\n⚙️ Preparing 'Identity.set_identity' for '{name}'...",
        "submitting": "🚀 Submitting transaction (waiting for inclusion)...",
        "success": "✅ SUCCESS! Node is now recognized as: {name}",
        "block": "📦 Block Hash: {hash}",
        "err_exec": "\n⚠️ Transaction included but failed. Check balance for deposit/fees.",
        "err_node": "❌ Node connection error:",
        "quit": "🛑 Returning to main menu..."
    },
    "es": {
        "title": " 🆔 GESTOR DE IDENTIDAD ON-CHAIN - ZKVERIFY",
        "conn": "📡 Conectando al entorno:",
        "sec_notice": "⚠️  SEGURIDAD: El mnemónico se procesa localmente y NUNCA se transmite.",
        "prompt_mne": "🔑 Ingresa el mnemónico (vacío para usar config.yaml): ",
        "wallet_ok": "🔓 Billetera desbloqueada: ",
        "err_wallet": "❌ Error al cargar billetera. Revisa el mnemónico.",
        "prompt_name": "\n📝 Ingresa el Nombre a mostrar (ej: RORU_NODE): ",
        "prep": "\n⚙️ Preparando 'Identity.set_identity' para '{name}'...",
        "submitting": "🚀 Enviando transacción (esperando inclusión)...",
        "success": "✅ ¡ÉXITO! El nodo ahora se reconoce como: {name}",
        "block": "📦 Hash del Bloque: {hash}",
        "err_exec": "\n⚠️ Transacción incluida pero fallida. Revisa el saldo para depósito/fees.",
        "err_node": "❌ Error de conexión al nodo:",
        "quit": "🛑 Volviendo al menú principal..."
    }
}

def run_identity_manager(override_env=None, override_lang=None):
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            env = override_env if override_env else config['network']['env']
            node_url = config['network']['endpoints'][env]
            lang = override_lang if override_lang else config.get('preferences', {}).get('language', 'en')
            conf_mnemonic = config['wallet'].get('mnemonic', "")
    except Exception as e:
        print(f"❌ Error YAML: {e}"); return

    t = TXT[lang] if lang in TXT else TXT["en"]
    print("\n" + "="*55 + f"\n {t['title']}\n" + "="*55)
    print(f"{t['conn']} {env.upper()} ({node_url})")

    try:
        substrate = SubstrateInterface(url=node_url)
    except Exception as e:
        print(f"{t['err_node']} {e}"); return

    print(f"\n{t['sec_notice']}")
    secret = getpass.getpass(t["prompt_mne"]).strip()
    if not secret: secret = conf_mnemonic

    try:
        keypair = Keypair.create_from_mnemonic(secret)
        print(f"{t['wallet_ok']} {keypair.ss58_address}")
    except Exception:
        print(t["err_wallet"]); time.sleep(2); return

    display_name = input(t["prompt_name"]).strip()
    if not display_name: return

    # Workaround SCALE BoundedVec [[]]
    identity_info = {
        'display': {'Raw': display_name},
        'legal': {'None': None},
        'web': {'None': None},
        'riot': {'None': None},
        'email': {'None': None},
        'pgp_fingerprint': None,
        'image': {'None': None},
        'twitter': {'None': None},
        'additional': [[]]
    }

    print(t["prep"].format(name=display_name))

    try:
        call = substrate.compose_call(
            call_module='Identity',
            call_function='set_identity',
            call_params={'info': identity_info}
        )
        extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)
        print(t["submitting"])
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        
        if receipt.is_success:
            print(f"\n{t['success'].format(name=display_name)}")
            print(t["block"].format(hash=receipt.block_hash))
        else:
            print(t["err_exec"])
            print(f"Error: {receipt.error_message}")
            
    except SubstrateRequestException as e:
        print(f"\n{t['err_node']} {e}")

    input("\nPress Enter to return...")

if __name__ == "__main__":
    run_identity_manager()
