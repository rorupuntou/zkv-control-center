import os
import sys
import yaml
import time

# --- IMPORTACIÓN DE TODOS LOS MÓDULOS CORE ---
from core.sentinel import run_sentinel
from core.block_inspector import run_block_master
from core.payout_automator import run_payout_automator
from core.paged_radar import run_paged_radar
from core.identity_manager import run_identity_manager
from core.gov_auditor import run_gov_auditor
from core.config_manager import run_config_manager
from core.nominator_wizard import run_nominator_wizard

# --- DICCIONARIO DEL MENÚ PRINCIPAL ---
TXT = {
    "en": {
        "title": "🚀 zkVerify Validator Control Center v1.0",
        "author": "by roru1312 | Uruguay Command Center 🇺🇾",
        "env": "🌐 Environment:",
        "lang": "🗣️  Language:",
        "menu": "What do you want to do today?",
        "opt_1": "1. 🛡️  Advanced Node Sentinel (Monitor)",
        "opt_2": "2. 🔍 Block Master CLI (Inspector)",
        "opt_3": "3. 💰 Auto-Payout Auditor (Rewards)",
        "opt_4": "4. 📡 Master Paged Radar (Staking Audit)",
        "opt_5": "5. 🆔 Identity Manager (Set On-Chain Name)",
        "opt_6": "6. 🏛️  Governance Auditor (OpenGov Scan)",
        "opt_7": "7. ⚙️  Configuration Manager (Keys & Addresses)",
        "opt_8": "8. 🧙‍♂️ Nominator Wizard (Staking Setup)",
        "opt_env": "9. 🔄 Switch Environment (Local/Volta/Mainnet)",
        "opt_lang": "10. 🌍 Switch Language (EN/ES)",
        "opt_exit": "0. ❌ Exit",
        "choice": "👉 Select an option: ",
        "bye": "👋 Closing Control Center. Happy Validating!",
        "invalid": "⚠️ Invalid option, please try again."
    },
    "es": {
        "title": "🚀 zkVerify Validator Control Center v1.0",
        "author": "por roru1312 | Uruguay Command Center 🇺🇾",
        "env": "🌐 Entorno:",
        "lang": "🗣️  Idioma:",
        "menu": "¿Qué deseas hacer hoy?",
        "opt_1": "1. 🛡️  Centinela Avanzado (Monitoreo)",
        "opt_2": "2. 🔍 Inspector de Bloques Maestro",
        "opt_3": "3. 💰 Auditor Automático de Pagos (Recompensas)",
        "opt_4": "4. 📡 Radar Maestro Paged (Auditoría Staking)",
        "opt_5": "5. 🆔 Gestor de Identidad (Nombre On-Chain)",
        "opt_6": "6. 🏛️  Auditor de Gobernanza (OpenGov)",
        "opt_7": "7. ⚙️  Gestor de Configuración (Llaves y Direcciones)",
        "opt_8": "8. 🧙‍♂️ Asistente de Nominación (Crear Staker)",
        "opt_env": "9. 🔄 Cambiar Entorno (Local/Volta/Mainnet)",
        "opt_lang": "10. 🌍 Cambiar Idioma (EN/ES)",
        "opt_exit": "0. ❌ Salir",
        "choice": "👉 Selecciona una opción: ",
        "bye": "👋 Cerrando Control Center. ¡Éxitos validando!",
        "invalid": "⚠️ Opción inválida, intenta de nuevo."
    }
}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_config():
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"❌ Error loading config.yaml: {e}")
        sys.exit(1)

def main():
    config = load_config()
    current_env = config['network']['env']
    current_lang = config.get('preferences', {}).get('language', 'en')

    # --- AUTO-SETUP CHECK (Detección de primer uso) ---
    wallet_mne = config.get('wallet', {}).get('mnemonic', '')
    stash_addr = config.get('validator', {}).get('stash_address', '')
    
    # Manejo seguro por si los campos vienen como 'None'
    wallet_mne = str(wallet_mne).strip() if wallet_mne else ""
    stash_addr = str(stash_addr).strip() if stash_addr else ""

    if not wallet_mne or not stash_addr:
        clear_screen()
        if current_lang == "es":
            print("\n" + "="*55)
            print(" 👋 ¡Bienvenido al zkVerify Control Center!")
            print("="*55)
            print("\n⚠️  Parece que es tu primera vez iniciando el programa.")
            print("Para poder firmar transacciones y auditar tu nodo,")
            print("necesitamos configurar tus credenciales primero.\n")
        else:
            print("\n" + "="*55)
            print(" 👋 Welcome to zkVerify Control Center!")
            print("="*55)
            print("\n⚠️  It looks like this is your first time here.")
            print("To sign transactions and audit your node properly,")
            print("we need to set up your public addresses first.\n")
        
        time.sleep(3)
        run_config_manager(override_lang=current_lang)
        
        # Recargar la configuración después de que el usuario la actualiza
        config = load_config()
    # ----------------------------------------------------

    while True:
        clear_screen()
        
        if current_lang not in TXT: current_lang = "en"
        t = TXT[current_lang]

        print("="*60)
        print(f"{t['title']:^60}")
        print(f"{t['author']:^60}")
        print("="*60)
        print(f" {t['env']} {current_env.upper()} | {t['lang']} {current_lang.upper()}")
        print("-" * 60)
        print(f" {t['menu']}\n")
        
        # Módulos Core
        print(f"  {t['opt_1']}")
        print(f"  {t['opt_2']}")
        print(f"  {t['opt_3']}")
        print(f"  {t['opt_4']}")
        print(f"  {t['opt_5']}")
        print(f"  {t['opt_6']}")
        print(f"  {t['opt_7']}")
        print(f"  {t['opt_8']}")
        print("\n  " + "."*35 + "\n")
        
        # Opciones de Entorno y Salida
        print(f"  {t['opt_env']}")
        print(f"  {t['opt_lang']}")
        print(f"  {t['opt_exit']}")
        print("="*60)

        choice = input(f"\n{t['choice']}").strip()

        if choice == '1':
            clear_screen(); run_sentinel(override_env=current_env, override_lang=current_lang)
        elif choice == '2':
            clear_screen(); run_block_master(override_env=current_env, override_lang=current_lang)
        elif choice == '3':
            clear_screen(); run_payout_automator(override_env=current_env, override_lang=current_lang)
        elif choice == '4':
            clear_screen(); run_paged_radar(override_env=current_env, override_lang=current_lang)
        elif choice == '5':
            clear_screen(); run_identity_manager(override_env=current_env, override_lang=current_lang)
        elif choice == '6':
            clear_screen(); run_gov_auditor(override_env=current_env, override_lang=current_lang)
        elif choice == '7':
            clear_screen(); run_config_manager(override_lang=current_lang)
            config = load_config() 
        elif choice == '8':
            clear_screen(); run_nominator_wizard(override_env=current_env, override_lang=current_lang)
        elif choice == '9':
            envs = ['local', 'volta', 'mainnet']
            idx = envs.index(current_env)
            current_env = envs[(idx + 1) % len(envs)]
        elif choice == '10':
            current_lang = "es" if current_lang == "en" else "en"
        elif choice == '0':
            print(f"\n{t['bye']}")
            break
        else:
            print(f"\n{t['invalid']}")
            time.sleep(1.5)

if __name__ == "__main__":
    main()
