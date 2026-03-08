import time
import yaml
import os
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

TXT = {
    "en": {
        "title": " 💰 AUTO-PAYOUT AUTOMATOR & AUDITOR (Final Version)",
        "conn": "📡 Connecting to environment:",
        "auth": "🔐 Authenticating wallet...",
        "stash": "🏦 Validator Stash:",
        "era_info": "📊 Current Network Era:",
        "audit_start": "🔍 Scanning eras {end} to {start}...",
        "era_claimed": "✅ Claimed",
        "era_pending": "💰 PENDING (Actionable!)",
        "era_inactive": "⚪ Inactive (No participation)",
        "prompt_era": "🔹 Enter Era, 'all' (claim pending), 'm' (older page), or 'q' (quit): ",
        "quit": "🛑 Returning to main menu...",
        "signing": "✍️  Signing transaction for Era",
        "success": "✅ Success! Payout confirmed in block hash:",
        "err_tx": "❌ Transaction failed:",
        "err_node": "❌ Node connection error:"
    },
    "es": {
        "title": " 💰 AUTOMATIZADOR DE PAGOS Y AUDITOR (Versión Final)",
        "conn": "📡 Conectando al entorno:",
        "auth": "🔐 Autenticando billetera...",
        "stash": "🏦 Stash del Validador:",
        "era_info": "📊 Era actual de la red:",
        "audit_start": "🔍 Escaneando eras de la {end} a la {start}...",
        "era_claimed": "✅ Cobrada",
        "era_pending": "💰 PENDIENTE (¡Lista para cobrar!)",
        "era_inactive": "⚪ Inactiva (Sin participación)",
        "prompt_era": "🔹 Ingresa Era, 'all' (cobrar pendientes), 'm' (página anterior), 'q' (salir): ",
        "quit": "🛑 Volviendo al menú principal...",
        "signing": "✍️  Firmando transacción para la Era",
        "success": "✅ ¡Éxito! Pago confirmado en el hash del bloque:",
        "err_tx": "❌ Transacción fallida:",
        "err_node": "❌ Error de conexión al nodo:"
    }
}

def check_era_status(substrate, era, stash):
    """
    Motor de detección INFALIBLE:
    Si la era no está cobrada y hay evidencia de premios en la red, 
    la marcamos como Pending para que el usuario pueda intentar el cobro.
    """
    # 1. ¿Ya está cobrada? (Esta es la única certeza absoluta de inactividad posterior)
    for map_name in ['ClaimedRewards']:
        try:
            # Revisamos ambas variantes de parámetros (era, stash) y (stash, era)
            if substrate.query('Staking', map_name, [era, stash]).value:
                return "claimed"
            if substrate.query('Staking', map_name, [stash, era]).value:
                return "claimed"
        except Exception:
            pass

    # 2. VERIFICACIÓN DE ACTIVIDAD (El "Detector de roru")
    # Si la era no está cobrada, buscamos CUALQUIER rastro de puntos o rewards
    try:
        # A. Revisamos puntos individuales (la forma estándar)
        reward_points = substrate.query('Staking', 'ErasRewardPoints', [era])
        if reward_points.value and 'individual' in reward_points.value:
            ind = reward_points.value['individual']
            # Detección flexible para dict o list de tuplas
            is_active = False
            if isinstance(ind, dict) and stash in ind: is_active = True
            elif isinstance(ind, list):
                for entry in ind:
                    if entry[0] == stash: 
                        is_active = True
                        break
            if is_active: return "pending"
    except Exception:
        pass

    # B. REVISIÓN DE SEGURIDAD: ¿Hay recompensas totales para esa era?
    # Si la red tiene un total de rewards para esa era > 0, y tú NO estás cobrado,
    # es mejor mostrarla como Pending que como Inactive.
    try:
        total_rewards = substrate.query('Staking', 'ErasValidatorReward', [era])
        if total_rewards.value and int(total_rewards.value) > 0:
            # Si hay plata en la era y no cobraste, te damos el beneficio de la duda
            return "pending"
    except Exception:
        pass

    # 3. Verificación de Staking (Overview) como última opción
    try:
        if substrate.query('Staking', 'ErasStakersOverview', [era, stash]).value:
            return "pending"
    except Exception:
        pass

    return "inactive"

def run_payout_automator(override_env=None, override_lang=None):
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            env = override_env if override_env else config['network']['env']
            node_url = config['network']['endpoints'][env]
            lang = config.get('preferences', {}).get('language', 'en')
            mnemonic = config['wallet']['mnemonic']
            stash_address = config['validator']['stash_address']
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    lang = override_lang if override_lang else lang
    t = TXT[lang] if lang in TXT else TXT["en"]

    print("\n" + "="*55)
    print(t["title"])
    print("="*55)
    print(f"{t['conn']} {env.upper()} ({node_url})")

    try:
        substrate = SubstrateInterface(url=node_url)
        print(t["auth"])
        keypair = Keypair.create_from_mnemonic(mnemonic)
    except Exception as e:
        print(f"{t['err_node']} {e}")
        return

    # Inicialización de Paginación
    active_era = substrate.query('Staking', 'ActiveEra').value['index']
    page_end = active_era - 1
    page_start = max(0, page_end - 9)

    while True:
        print("-" * 40)
        print(f"{t['era_info']} {active_era}")
        print(f"\n{t['audit_start'].format(end=page_end, start=page_start)}")
        
        pending_in_page = []

        print("\n--- 📊 Status ---")
        for e in range(page_end, page_start - 1, -1):
            status = check_era_status(substrate, e, stash_address)
            if status == "claimed":
                print(f"  🔹 Era {e:03d}: {t['era_claimed']}")
            elif status == "pending":
                print(f"  🔹 Era {e:03d}: {t['era_pending']}")
                pending_in_page.append(e)
            else:
                print(f"  🔹 Era {e:03d}: {t['era_inactive']}")
        print("-----------------\n")

        cmd = input(t["prompt_era"]).strip().lower()

        if cmd == 'q': break
        elif cmd == 'm':
            page_end = page_start - 1
            page_start = max(0, page_end - 9)
            continue
        
        to_process = pending_in_page if cmd == 'all' else ([int(cmd)] if cmd.isdigit() else [])
        
        for era in to_process:
            print(f"\n{t['signing']} {era}...")
            try:
                call = substrate.compose_call('Staking', 'payout_stakers', {'validator_stash': stash_address, 'era': era})
                extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)
                receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
                if receipt.is_success:
                    print(f"{t['success']} {receipt.block_hash}")
                else:
                    print(f"{t['err_tx']} {receipt.error_message}")
            except Exception as e:
                print(f"❌ Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    run_payout_automator()
