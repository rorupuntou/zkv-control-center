import os
import yaml
import time
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

TXT = {
    "en": {
        "title": "🧙‍♂️ NOMINATOR WIZARD: STAKING SETUP",
        "fetch": "🔍 Fetching and ranking validators by lowest commission...",
        "list_title": "🏆 TOP VALIDATORS (Sorted by lowest commission)",
        "select_prompt": "👉 Enter the numbers of the validators you want to nominate (comma separated, e.g. 1,3,5): ",
        "amount_prompt": "💰 Enter the amount of VFY to bond (lock): ",
        "confirm": "⚠️ You are about to bond {amt} VFY and nominate {count} validators. Proceed? (y/N): ",
        "signing": "✍️ Signing and sending transaction...",
        "success": "✅ Transaction successful! Hash: {hash}",
        "err_keys": "❌ No mnemonic found in config.yaml. Please set it up first.",
        "err_tx": "❌ Transaction failed: {err}",
        "err_node": "❌ Connection failed: "
    },
    "es": {
        "title": "🧙‍♂️ ASISTENTE DE NOMINACIÓN: CONFIGURACIÓN DE STAKING",
        "fetch": "🔍 Buscando y ordenando validadores por menor comisión...",
        "list_title": "🏆 MEJORES VALIDADORES (Ordenados por menor comisión)",
        "select_prompt": "👉 Ingresa los números de los validadores a nominar (separados por coma, ej: 1,3,5): ",
        "amount_prompt": "💰 Ingresa la cantidad de VFY a lockear (Bond): ",
        "confirm": "⚠️ Vas a lockear {amt} VFY y nominar {count} validadores. ¿Proceder? (y/N): ",
        "signing": "✍️ Firmando y enviando transacción...",
        "success": "✅ ¡Transacción exitosa! Hash: {hash}",
        "err_keys": "❌ No se encontró la frase semilla (mnemonic) en config.yaml.",
        "err_tx": "❌ La transacción falló: {err}",
        "err_node": "❌ Error de conexión: "
    }
}

def load_config_and_keys():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def get_validator_commission(substrate, stash_address):
    try:
        prefs = substrate.query('Staking', 'Validators', [stash_address])
        if prefs.value and 'commission' in prefs.value:
            return prefs.value['commission'] / 10_000_000
    except: pass
    return 0.0

def run_nominator_wizard(override_env=None, override_lang=None):
    try:
        config = load_config_and_keys()
        env = override_env if override_env else config['network']['env']
        node_url = config['network']['endpoints'][env]
        lang = override_lang if override_lang else config.get('preferences', {}).get('language', 'en')
        mnemonic = config.get('wallet', {}).get('mnemonic', '')
    except Exception as e:
        print(f"❌ Error YAML: {e}"); return

    t = TXT[lang] if lang in TXT else TXT["en"]
    print("\n" + "="*60 + f"\n {t['title']}\n" + "="*60)

    if not mnemonic:
        print(f"\n{t['err_keys']}")
        input("\nPress Enter to return...")
        return

    try:
        substrate = SubstrateInterface(url=node_url)
        keypair = Keypair.create_from_mnemonic(mnemonic)
    except Exception as e:
        print(f"{t['err_node']} {e}"); return

    # 1. Obtener y ordenar validadores
    print(f"\n{t['fetch']}")
    active_validators = substrate.query('Session', 'Validators').value
    
    val_data = []
    for v in active_validators:
        comm = get_validator_commission(substrate, v)
        val_data.append({"address": v, "commission": comm})
    
    # Ordenar de menor a mayor comisión
    val_data.sort(key=lambda x: x["commission"])

    print(f"\n{t['list_title']}")
    for i, v in enumerate(val_data[:20], 1): # Mostramos los mejores 20
        print(f" [{i:02d}] {v['address']} | Com: {v['commission']:>5.2f}%")

    # 2. Selección del usuario
    selection = input(f"\n{t['select_prompt']}").strip()
    if not selection: return
    
    try:
        selected_indices = [int(x.strip()) - 1 for x in selection.split(",")]
        targets = [val_data[i]["address"] for i in selected_indices if 0 <= i < len(val_data)]
    except:
        return

    if not targets: return

    # 3. Monto a lockear
    try:
        amount_vfy = float(input(f"\n{t['amount_prompt']}").strip())
        amount_plancks = int(amount_vfy * 10**18) # Ajustar según los decimales de VFY
    except:
        return

    # 4. Confirmación
    confirm = input(f"\n{t['confirm'].format(amt=amount_vfy, count=len(targets))}").strip().lower()
    if confirm != 'y': return

# 5. Armar y enviar transacción
    print(f"\n{t['signing']}")
    try:
        # Verificamos si la cuenta YA tiene fondos bonded
        ledger = substrate.query('Staking', 'Ledger', [keypair.ss58_address]).value
        
        calls = []
        if ledger:
            # Si ya está bonded, usamos bond_extra en lugar de bond
            print("  ℹ️ Account already bonded. Adding extra funds instead of creating a new bond.")
            call_bond_extra = substrate.compose_call(
                call_module='Staking',
                call_function='bond_extra',
                call_params={'max_additional': amount_plancks}
            )
            calls.append(call_bond_extra)
        else:
            # Si es la primera vez, usamos bond
            call_bond = substrate.compose_call(
                call_module='Staking',
                call_function='bond',
                call_params={
                    'value': amount_plancks,
                    'payee': 'Staked'
                }
            )
            calls.append(call_bond)

        # Siempre agregamos la nominación
        call_nominate = substrate.compose_call(
            call_module='Staking',
            call_function='nominate',
            call_params={'targets': targets}
        )
        calls.append(call_nominate)

        # Batch: Ejecutar todo junto
        call_batch = substrate.compose_call(
            call_module='Utility',
            call_function='batch_all',
            call_params={'calls': calls}
        )

        extrinsic = substrate.create_signed_extrinsic(call=call_batch, keypair=keypair)
        receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
        
        if receipt.is_success:
            print(f"\n{t['success'].format(hash=receipt.extrinsic_hash)}")
        else:
            print(f"\n{t['err_tx'].format(err=receipt.error_message)}")

    except SubstrateRequestException as e:
        print(f"\n{t['err_tx'].format(err=str(e))}")

    input("\nPress Enter to continue...")
