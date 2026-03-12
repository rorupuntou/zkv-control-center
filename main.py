import os
import sys
import yaml
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt

# --- IMPORTACIÓN DE TODOS LOS MÓDULOS CORE ---
from core.sentinel import run_sentinel
from core.block_inspector import run_block_master
from core.payout_automator import run_payout_automator
from core.paged_radar import run_paged_radar
from core.identity_manager import run_identity_manager
from core.gov_auditor import run_gov_auditor
from core.config_manager import run_config_manager
from core.nominator_wizard import run_nominator_wizard

console = Console()

# --- DICCIONARIO DEL MENÚ PRINCIPAL ---
TXT = {
    "en": {
        "title": "🚀 zkVerify Validator Control Center v1.0",
        "author": "by roru1312 | Uruguay Command Center 🇺🇾",
        "env": "🌐 Environment",
        "lang": "🗣️  Language",
        "menu": "What do you want to do today?",
        "opt_1": "1. 🛡️  Advanced Node Sentinel",
        "opt_2": "2. 🔍 Block Master CLI",
        "opt_3": "3. 💰 Auto-Payout Auditor",
        "opt_4": "4. 📡 Master Paged Radar",
        "opt_5": "5. 🆔 Identity Manager",
        "opt_6": "6. 🏛️  Governance Auditor",
        "opt_7": "7. ⚙️  Configuration Manager",
        "opt_8": "8. 🧙‍♂️ Nominator Wizard",
        "opt_env": "9. 🔄 Switch Environment",
        "opt_lang": "10. 🌍 Switch Language",
        "opt_exit": "0. ❌ Exit",
        "choice": "👉 Select an option",
        "bye": "👋 Closing Control Center. Happy Validating!",
        "invalid": "⚠️ Invalid option, please try again."
    },
    "es": {
        "title": "🚀 zkVerify Validator Control Center v1.0",
        "author": "por roru1312 | Uruguay Command Center 🇺🇾",
        "env": "🌐 Entorno",
        "lang": "🗣️  Idioma",
        "menu": "¿Qué deseas hacer hoy?",
        "opt_1": "1. 🛡️  Centinela Avanzado",
        "opt_2": "2. 🔍 Inspector de Bloques",
        "opt_3": "3. 💰 Auditor de Recompensas",
        "opt_4": "4. 📡 Radar Maestro Paged",
        "opt_5": "5. 🆔 Gestor de Identidad",
        "opt_6": "6. 🏛️  Auditor de Gobernanza",
        "opt_7": "7. ⚙️  Gestor de Configuración",
        "opt_8": "8. 🧙‍♂️ Asistente de Nominación",
        "opt_env": "9. 🔄 Cambiar Entorno",
        "opt_lang": "10. 🌍 Cambiar Idioma",
        "opt_exit": "0. ❌ Salir",
        "choice": "👉 Selecciona una opción",
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
        console.print(f"[bold red]❌ Error loading config.yaml: {e}[/bold red]")
        sys.exit(1)

def main():
    config = load_config()
    current_env = config.get('network', {}).get('env', 'local')
    current_lang = config.get('preferences', {}).get('language', 'en')

    # --- AUTO-SETUP CHECK ---
    wallet_mne = str(config.get('wallet', {}).get('mnemonic', '')).strip()
    stash_addr = str(config.get('validator', {}).get('stash_address', '')).strip()

    if not wallet_mne or not stash_addr or wallet_mne == "None":
        clear_screen()
        welcome_text = "⚠️ Parece que es tu primera vez iniciando el programa.\nPara poder firmar transacciones, necesitamos configurar tus credenciales." if current_lang == "es" else "⚠️ It looks like this is your first time here.\nTo sign transactions, we need to set up your keys."
        
        console.print(Panel(welcome_text, title="[bold cyan]👋 Welcome to zkVerify Control Center![/bold cyan]", border_style="cyan", padding=(1, 2)))
        time.sleep(3)
        run_config_manager(override_lang=current_lang)
        config = load_config()

    while True:
        clear_screen()
        if current_lang not in TXT: current_lang = "en"
        t = TXT[current_lang]

        # --- CONSTRUCCIÓN DE LA INTERFAZ CON RICH ---
        header = Text()
        header.append(f"{t['title']}\n", style="bold cyan")
        header.append(f"{t['author']}", style="dim italic")
        console.print(Panel(header, border_style="cyan", expand=False))

        status_table = Table(show_header=False, box=None, expand=False)
        status_table.add_row(f"[bold yellow]{t['env']}:[/bold yellow] [green]{current_env.upper()}[/green]", f"[bold yellow]{t['lang']}:[/bold yellow] [green]{current_lang.upper()}[/green]")
        console.print(Panel(status_table, border_style="yellow", expand=False))

        menu_table = Table(show_header=False, box=None, padding=(0, 2))
        menu_table.add_row(f"[cyan]{t['opt_1']}[/cyan]", f"[magenta]{t['opt_7']}[/magenta]")
        menu_table.add_row(f"[cyan]{t['opt_2']}[/cyan]", f"[magenta]{t['opt_8']}[/magenta]")
        menu_table.add_row(f"[cyan]{t['opt_3']}[/cyan]", "")
        menu_table.add_row(f"[cyan]{t['opt_4']}[/cyan]", f"[blue]{t['opt_env']}[/blue]")
        menu_table.add_row(f"[cyan]{t['opt_5']}[/cyan]", f"[blue]{t['opt_lang']}[/blue]")
        menu_table.add_row(f"[cyan]{t['opt_6']}[/cyan]", f"[red]{t['opt_exit']}[/red]")
        
        console.print(Panel(menu_table, title=f"[bold green]{t['menu']}[/bold green]", border_style="green", expand=False))

        choice = Prompt.ask(f"[bold yellow]{t['choice']}[/bold yellow]")

        # --- LÓGICA DE NAVEGACIÓN ---
        if choice == '1': clear_screen(); run_sentinel(override_env=current_env, override_lang=current_lang)
        elif choice == '2': clear_screen(); run_block_master(override_env=current_env, override_lang=current_lang)
        elif choice == '3': clear_screen(); run_payout_automator(override_env=current_env, override_lang=current_lang)
        elif choice == '4': clear_screen(); run_paged_radar(override_env=current_env, override_lang=current_lang)
        elif choice == '5': clear_screen(); run_identity_manager(override_env=current_env, override_lang=current_lang)
        elif choice == '6': clear_screen(); run_gov_auditor(override_env=current_env, override_lang=current_lang)
        elif choice == '7': 
            clear_screen(); run_config_manager(override_lang=current_lang)
            config = load_config() 
        elif choice == '8': clear_screen(); run_nominator_wizard(override_env=current_env, override_lang=current_lang)
        elif choice == '9':
            envs = ['local', 'volta', 'mainnet']
            current_env = envs[(envs.index(current_env) + 1) % len(envs)]
        elif choice == '10':
            current_lang = "es" if current_lang == "en" else "en"
        elif choice == '0':
            console.print(f"\n[bold green]{t['bye']}[/bold green]")
            break
        else:
            console.print(f"\n[bold red]{t['invalid']}[/bold red]")
            time.sleep(1.5)

if __name__ == "__main__":
    main()
