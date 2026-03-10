import time
import yaml
import os
from substrateinterface import SubstrateInterface

TXT = {
    "en": {
        "title": "📡 ZKVERIFY MASTER RADAR: HYBRID PAGED AUDITOR",
        "conn": "📡 Connecting to environment:",
        "era_info": "📊 Current Network Era:",
        "menu_1": "1. Scan Active Set (List & Select)",
        "menu_2": "2. Manual Entry (Direct Stash Audit)",
        "menu_q": "q. Return to main menu",
        "choice": "Select an option: ",
        "fetch": "🔍 Fetching Session.Validators...",
        "found": "✅ Found {count} active validators.",
        "disp_1": "1. Show TOP 5 (Fastest)",
        "disp_2": "2. Show ALL (Full List with Stake info)",
        "list_title": "--- Current Active Set List ---",
        "idx_prompt": "Enter index to audit (1-{count}): ",
        "manual_prompt": "📝 Enter Validator Stash Address: ",
        "report_title": "📊 STAKING REPORT",
        "total_stk": "💰 Total Stake:",
        "self_stk": "🔐 Self-Bonded:",
        "nom_stk": "🤝 From Nominators:",
        "pages": "📄 Data Pages:",
        "nom_found": "👥 Total Nominators Found:",
        "nom_top": "🏆 TOP 10 NOMINATORS (RANKED BY STAKE):",
        "self_only": "ℹ️ This validator is operating with 100% self-bonded funds.",
        "err_no_data": "❌ No active staking data found for this address.",
        "err_node": "❌ Connection failed:"
    },
    "es": {
        "title": "📡 RADAR MAESTRO ZKVERIFY: AUDITOR PAGINADO HÍBRIDO",
        "conn": "📡 Conectando al entorno:",
        "era_info": "📊 Era actual de la red:",
        "menu_1": "1. Escanear Set Activo (Listar y Seleccionar)",
        "menu_2": "2. Entrada Manual (Auditoría Directa)",
        "menu_q": "q. Volver al menú principal",
        "choice": "Selecciona una opción: ",
        "fetch": "🔍 Obteniendo Session.Validators...",
        "found": "✅ Se encontraron {count} validadores activos.",
        "disp_1": "1. Ver TOP 5 (Más rápido)",
        "disp_2": "2. Ver TODOS (Lista completa con Stake)",
        "list_title": "--- Lista del Set Activo Actual ---",
        "idx_prompt": "Ingresa el índice para auditar (1-{count}): ",
        "manual_prompt": "📝 Ingresa la dirección Stash del Validador: ",
        "report_title": "📊 REPORTE DE STAKING",
        "total_stk": "💰 Stake Total:",
        "self_stk": "🔐 Auto-Bonded:",
        "nom_stk": "🤝 De Nominadores:",
        "pages": "📄 Páginas de Datos:",
        "nom_found": "👥 Total de Nominadores Encontrados:",
        "nom_top": "🏆 TOP 10 NOMINADORES (POR STAKE):",
        "self_only": "ℹ️ Este validador opera 100% con fondos propios.",
        "err_no_data": "❌ No hay datos de staking activos para esta dirección.",
        "err_node": "❌ Error de conexión:"
    }
}

def get_total_stake(substrate, stash, era):
    try:
        overview = substrate.query('Staking', 'ErasStakersOverview', [era, stash]).value
        return overview['total'] / 10**18 if overview else 0.0
    except: return 0.0

def get_validator_commission(substrate, stash_address):
    """
    Consulta la comisión configurada por el validador.
    El valor se guarda como un 'Perbill' (partes por billón).
    """
    try:
        prefs = substrate.query('Staking', 'Validators', [stash_address])
        if prefs.value and 'commission' in prefs.value:
            # Convertimos Perbill a porcentaje (100% = 1,000,000,000)
            return prefs.value['commission'] / 10_000_000
    except Exception:
        pass
    return 0.0

def audit_validator(substrate, target_stash, active_era, t):
    try:
        overview = substrate.query('Staking', 'ErasStakersOverview', [active_era, target_stash]).value
        if not overview:
            print(f"\n{t['err_no_data']}")
            return

        total_vfy = overview['total'] / 10**18
        own_vfy = overview['own'] / 10**18
        pages = overview['page_count']

        print("\n" + "—"*65)
        print(f"{t['report_title']} | Era: {active_era}")
        print(f"🔑 Stash: {target_stash}")
        print("—"*65)
        print(f"{t['total_stk']:<20} {total_vfy:,.2f} VFY")
        print(f"{t['self_stk']:<20} {own_vfy:,.2f} VFY")
        print(f"{t['nom_stk']:<20} {total_vfy - own_vfy:,.2f} VFY")
        print(f"{t['pages']:<20} {pages}")
        print("—"*65)

        all_nominators = []
        for p in range(pages):
            page_data = substrate.query('Staking', 'ErasStakersPaged', [active_era, target_stash, p]).value
            if page_data and 'others' in page_data:
                all_nominators.extend(page_data['others'])

        if all_nominators:
            print(f"{t['nom_found']} {len(all_nominators)}")
            print(f"\n{t['nom_top']}")
            sorted_noms = sorted(all_nominators, key=lambda x: x['value'], reverse=True)
            for i, nom in enumerate(sorted_noms[:10], 1):
                amount = nom['value'] / 10**18
                share = (amount / total_vfy) * 100
                print(f"  {i:02d}. {nom['who']} -> {amount:,.2f} VFY ({share:.2f}%)")
        else:
            print(f"\n{t['self_only']}")
        print("—"*65)
    except Exception as e: print(f"❌ Error: {e}")

def run_paged_radar(override_env=None, override_lang=None):
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

    while True:
        active_era = substrate.query('Staking', 'ActiveEra').value['index']
        print(f"\n{t['era_info']} {active_era}")
        print(f" {t['menu_1']}\n {t['menu_2']}\n {t['menu_q']}")
        
        choice = input(f"\n{t['choice']}").strip().lower()
        if choice == 'q': break

        target_stash = ""
        if choice == '1':
            print(f"\n{t['fetch']}")
            active_validators = substrate.query('Session', 'Validators').value
            if not active_validators: continue
            
            print(t['found'].format(count=len(active_validators)))
            print(f" {t['disp_1']}\n {t['disp_2']}")
            sub_c = input(f"\n{t['choice']}").strip()
            
            list_to_show = active_validators[:5] if sub_c == '1' else active_validators
            print(f"\n{t['list_title']}")
            for i, v in enumerate(list_to_show, 1):
                stake = get_total_stake(substrate, v, active_era)
                comm = get_validator_commission(substrate, v)
                
                # Aquí se formatea el Stake y la Comisión alineada a la derecha
                print(f" [{i:02d}] {v} | Stake: {stake:12,.2f} VFY | Com: {comm:>5.2f}%")
            
            try:
                idx = int(input(f"\n{t['idx_prompt'].format(count=len(list_to_show))}")) - 1
                if 0 <= idx < len(list_to_show): target_stash = list_to_show[idx]
            except: continue

        elif choice == '2':
            target_stash = input(f"\n{t['manual_prompt']}").strip()

        if target_stash:
            audit_validator(substrate, target_stash, active_era, t)
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    run_paged_radar()
