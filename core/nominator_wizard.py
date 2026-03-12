import os
import yaml
import time
from substrateinterface import SubstrateInterface, Keypair
from substrateinterface.exceptions import SubstrateRequestException

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt

console = Console()

TXT = {
    "en": {
        "title": "🧙‍♂️ NOMINATOR WIZARD: STAKING CENTER",
        "fetch": "🔍 Fetching your on-chain profile...",
        "profile_title": "👤 YOUR CURRENT STAKING PROFILE",
        "menu_opt1": "1. 📊 Analyze My Current Nominations",
        "menu_opt2": "2. 🔍 Explore Top 20 & Nominate",
        "menu_opt0": "0. 🔙 Return to Main Menu",
        "choice": "👉 Select an option",
        "analyzing": "🔍 Analyzing your current targets & Phragmén distribution...",
        "table_current": "📊 YOUR NOMINATED VALIDATORS (Live Status)",
        "exploring": "🔍 Scanning the network and calculating reward projections...",
        "table_top": "🏆 TOP VALIDATORS (Ranked by Highest Estimated Return)",
        "select_prompt": "👉 Enter the numbers of the validators you want to nominate (comma separated)",
        "amount_prompt": "💰 Enter the amount of VFY to bond/add (lock)",
        "confirm": "⚠️ You are about to lock [bold cyan]{amt} VFY[/bold cyan] and nominate [bold cyan]{count} validators[/bold cyan]. Proceed?",
        "signing": "✍️  Signing and sending transaction...",
        "success": "✅ Transaction successful! Hash: {hash}",
        "err_keys": "❌ No mnemonic found in config.yaml. Please set it up first.",
        "err_tx": "❌ Transaction failed: {err}",
        "err_node": "❌ Connection failed: "
    },
    "es": {
        "title": "🧙‍♂️ ASISTENTE DE NOMINACIÓN: CENTRO DE STAKING",
        "fetch": "🔍 Consultando tu perfil en la blockchain...",
        "profile_title": "👤 TU PERFIL DE STAKING ACTUAL",
        "menu_opt1": "1. 📊 Analizar mis Nominaciones Actuales",
        "menu_opt2": "2. 🔍 Explorar el Top 20 y Nominar",
        "menu_opt0": "0. 🔙 Volver al Menú Principal",
        "choice": "👉 Selecciona una opción",
        "analyzing": "🔍 Analizando tus validadores y distribución de Phragmén...",
        "table_current": "📊 TUS VALIDADORES NOMINADOS (Estado en Vivo)",
        "exploring": "🔍 Escaneando la red y calculando proyecciones de recompensas...",
        "table_top": "🏆 TOP VALIDADORES (Rankeados por Mayor Retorno Estimado)",
        "select_prompt": "👉 Ingresa los números a nominar (separados por coma, ej: 1,3,5)",
        "amount_prompt": "💰 Ingresa la cantidad de VFY a lockear/agregar",
        "confirm": "⚠️ Vas a lockear [bold cyan]{amt} VFY[/bold cyan] y nominar a [bold cyan]{count} validadores[/bold cyan]. ¿Proceder?",
        "signing": "✍️  Firmando y enviando transacción...",
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

def get_era_and_actives(substrate):
    active_era_data = substrate.query('Staking', 'ActiveEra').value
    current_era = active_era_data.get('index', 0) if active_era_data else 0
    active_validators = [a.value for a in substrate.query('Session', 'Validators')]
    return current_era, active_validators

def get_validator_total_stake(substrate, era, account_id):
    try:
        overview = substrate.query('Staking', 'ErasStakersOverview', [era, account_id]).value
        if overview and 'total' in overview: return int(str(overview['total']).replace(',', '')) / 10**18
    except: pass
    try:
        exp = substrate.query('Staking', 'ErasStakers', [era, account_id]).value
        if exp and 'total' in exp: return int(str(exp['total']).replace(',', '')) / 10**18
    except: pass
    return 0.0

def get_my_allocated_stake(substrate, era, val_account, my_account):
    try:
        exp = substrate.query('Staking', 'ErasStakers', [era, val_account]).value
        if exp and 'others' in exp:
            for nominator in exp['others']:
                if nominator['who'] == my_account:
                    return int(str(nominator['value']).replace(',', '')) / 10**18
    except: pass
    return 0.0

def get_avg_validator_reward(substrate, current_era, total_validators):
    if total_validators == 0 or current_era == 0: return 0.0
    try:
        last_era_reward = substrate.query('Staking', 'ErasValidatorReward', [current_era - 1]).value
        if last_era_reward:
            total_vfy = int(str(last_era_reward).replace(',', '')) / 10**18
            return total_vfy / total_validators
    except: pass
    return 0.0

def format_address(addr):
    """Trunca la dirección para que se vea bien en tablas pequeñas"""
    return f"{addr[:10]}...{addr[-8:]}" if len(addr) > 20 else addr

def run_nominator_wizard(override_env=None, override_lang=None):
    try:
        config = load_config_and_keys()
        env = override_env if override_env else config['network']['env']
        node_url = config['network']['endpoints'][env]
        lang = override_lang if override_lang else config.get('preferences', {}).get('language', 'en')
        mnemonic = config.get('wallet', {}).get('mnemonic', '')
    except Exception as e:
        console.print(f"[bold red]❌ Error YAML: {e}[/bold red]"); return

    t = TXT[lang] if lang in TXT else TXT["en"]
    
    if not mnemonic or mnemonic == "None":
        console.print(f"\n[bold red]{t['err_keys']}[/bold red]")
        Prompt.ask("\n[dim]Press Enter to return...[/dim]")
        return

    try:
        substrate = SubstrateInterface(url=node_url)
        keypair = Keypair.create_from_mnemonic(mnemonic)
    except Exception as e:
        console.print(f"[bold red]{t['err_node']} {e}[/bold red]"); return

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        console.print(f"\n[bold magenta]{t['title']}[/bold magenta]")
        console.print("="*85)
        console.print(f"[cyan]{t['fetch']}[/cyan]\n")

        bonded_amt = 0.0
        current_targets = []
        
        ledger = substrate.query('Staking', 'Ledger', [keypair.ss58_address]).value
        if ledger:
            bonded_amt = int(str(ledger.get('active', 0)).replace(',', '')) / 10**18
            
        nominator_info = substrate.query('Staking', 'Nominators', [keypair.ss58_address]).value
        if nominator_info:
            current_targets = nominator_info.get('targets', [])

        profile_text = Text()
        profile_text.append(f"Public Key: ", style="bold")
        profile_text.append(f"{keypair.ss58_address}\n", style="cyan")
        profile_text.append(f"Bonded VFY: ", style="bold")
        profile_text.append(f"{bonded_amt:,.2f} VFY\n", style="green" if bonded_amt > 0 else "red")
        
        if current_targets:
            profile_text.append(f"Nominating: ", style="bold")
            profile_text.append(f"{len(current_targets)} Validators", style="yellow")
        else:
            profile_text.append(f"Status: ", style="bold")
            profile_text.append(f"Not nominating currently", style="dim")

        console.print(Panel(profile_text, title=f"[bold blue]{t['profile_title']}[/bold blue]", border_style="blue", expand=False))

        console.print(f"\n[bold]{t['menu_opt1']}[/bold]")
        console.print(f"[bold]{t['menu_opt2']}[/bold]")
        console.print(f"[dim]{t['menu_opt0']}[/dim]\n")

        choice = Prompt.ask(f"[bold yellow]{t['choice']}[/bold yellow]", choices=["1", "2", "0"])

        if choice == "0":
            break

        elif choice == "1":
            if not current_targets:
                console.print("\n[yellow]⚠️ You are not nominating any validators yet.[/yellow]")
                Prompt.ask("\n[dim]Press Enter to continue...[/dim]")
                continue

            console.print(f"\n[cyan]{t['analyzing']}[/cyan]")
            current_era, active_validators = get_era_and_actives(substrate)
            
            table = Table(title=f"\n[bold yellow]{t['table_current']}[/bold yellow]", show_lines=True)
            table.add_column("Status", justify="center")
            table.add_column("Validator Address", style="green")
            table.add_column("Current Stake", justify="right", style="blue")
            table.add_column("Comm", justify="right", style="magenta")
            table.add_column("My Allocated VFY", justify="right", style="yellow") 

            for val_addr in current_targets:
                is_active = val_addr in active_validators
                status = "Active 🟢" if is_active else "Waiting ⏳"
                
                prefs = substrate.query('Staking', 'Validators', [val_addr]).value
                comm = (prefs.get('commission', 0) / 10_000_000) if prefs else 0.0
                
                stake = get_validator_total_stake(substrate, current_era, val_addr) if is_active else 0.0
                stake_str = f"{stake:,.0f} VFY" if stake > 0 else "Waiting Era"
                
                my_allocation = get_my_allocated_stake(substrate, current_era, val_addr, keypair.ss58_address) if is_active else 0.0
                alloc_str = f"{my_allocation:,.2f} VFY" if my_allocation > 0 else "Pending ⏳"
                
                # Usamos el truncamiento visual
                table.add_row(status, format_address(val_addr), stake_str, f"{comm:>5.2f}%", alloc_str)
            
            console.print(table)
            Prompt.ask("\n[dim]Press Enter to return...[/dim]")

        elif choice == "2":
            console.print(f"\n[cyan]{t['exploring']}[/cyan]")
            current_era, active_validators = get_era_and_actives(substrate)
            all_prefs = substrate.query_map('Staking', 'Validators')

            avg_reward = get_avg_validator_reward(substrate, current_era, len(active_validators))

            val_data = []
            for account, prefs in all_prefs:
                addr = account.value
                comm = prefs.value.get('commission', 0) / 10_000_000
                is_active = addr in active_validators
                
                stake = get_validator_total_stake(substrate, current_era, addr) if is_active else 0.0
                
                est_share = 0.0
                est_vfy_reward = 0.0
                if bonded_amt > 0:
                    total_proj = stake + bonded_amt
                    est_share = (bonded_amt / total_proj) if total_proj > 0 else 0.0
                    est_vfy_reward = avg_reward * est_share * (1 - (comm / 100))

                val_data.append({
                    "address": addr, "full_address": addr, "commission": comm, "is_active": is_active,
                    "stake": stake, "est_share": est_share * 100, "est_reward": est_vfy_reward
                })
            
            # ORDENAMIENTO SUPREMO: Primero activos, luego por quien te da más recompensa VFY
            val_data.sort(key=lambda x: (not x["is_active"], -x["est_reward"], -x["stake"]))

            table = Table(title=f"\n[bold yellow]{t['table_top']}[/bold yellow]", show_lines=True)
            table.add_column("Nº", justify="center", style="cyan")
            table.add_column("Status", justify="center")
            table.add_column("Validator Address", style="green")
            table.add_column("Total Stake", justify="right", style="blue")
            table.add_column("Comm", justify="right", style="magenta")
            table.add_column("Est. Share", justify="right", style="yellow")
            table.add_column("~ Reward/Era", justify="right", style="bold green") 

            top_20 = val_data[:20]
            for i, v in enumerate(top_20, 1):
                status = "Active 🟢" if v['is_active'] else "Waiting ⏳"
                stake_str = f"{v['stake']:,.0f} VFY" if v['stake'] > 0 else "0 VFY"
                share_str = f"{v['est_share']:.4f}%" if v['est_share'] > 0 else "-"
                reward_str = f"~ {v['est_reward']:.2f} VFY" if v['est_reward'] > 0 else "-"
                
                table.add_row(f"{i:02d}", status, format_address(v['full_address']), stake_str, f"{v['commission']:>5.2f}%", share_str, reward_str)
            
            console.print(table)

            selection = Prompt.ask(f"\n[bold yellow]{t['select_prompt']}[/bold yellow]")
            if not selection: continue
            
            try:
                selected_indices = [int(x.strip()) - 1 for x in selection.split(",")]
                targets = [top_20[i]["full_address"] for i in selected_indices if 0 <= i < len(top_20)]
            except:
                console.print("[bold red]⚠️ Invalid selection.[/bold red]"); time.sleep(1.5); continue

            if not targets: continue

            try:
                amount_str = Prompt.ask(f"\n[bold yellow]{t['amount_prompt']}[/bold yellow]")
                amount_vfy = float(amount_str.strip())
                amount_plancks = int(amount_vfy * 10**18) 
            except: continue

            confirm = Prompt.ask(f"\n{t['confirm'].format(amt=amount_vfy, count=len(targets))}", choices=["y", "n"], default="n")
            if confirm != 'y': continue

            console.print(f"\n[bold cyan]{t['signing']}[/bold cyan]")
            try:
                calls = []
                if bonded_amt > 0:
                    calls.append(substrate.compose_call('Staking', 'bond_extra', {'max_additional': amount_plancks}))
                else:
                    calls.append(substrate.compose_call('Staking', 'bond', {'value': amount_plancks, 'payee': 'Staked'}))

                calls.append(substrate.compose_call('Staking', 'nominate', {'targets': targets}))
                call_batch = substrate.compose_call('Utility', 'batch_all', {'calls': calls})

                extrinsic = substrate.create_signed_extrinsic(call=call_batch, keypair=keypair)
                receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
                
                if receipt.is_success:
                    console.print(f"\n[bold green]{t['success'].format(hash=receipt.extrinsic_hash)}[/bold green]")
                else:
                    console.print(f"\n[bold red]{t['err_tx'].format(err=receipt.error_message)}[/bold red]")

            except SubstrateRequestException as e:
                console.print(f"\n[bold red]{t['err_tx'].format(err=str(e))}[/bold red]")

            Prompt.ask("\n[dim]Press Enter to continue...[/dim]")
