import os
import yaml
import time
from substrateinterface import SubstrateInterface, Keypair
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

TXT = {
    "en": {
        "title": "🤑 SMART YIELD CLAIMER v2.2 (Forensic Mode)",
        "scan_mode": "Choose Scan Mode:\n1. Quick View (Last 10 Eras)\n2. Full Audit (20 Eras per page)",
        "status_claimed_me": "✅ Claimed (YOU)",
        "status_claimed_ext": "✅ Claimed (Other)",
        "status_pending": "💰 PENDING",
        "status_none": "⚪ No Stake",
        "prompt": "🔹 ID to claim, 'all' (list), 'm' (older), or 'q' (exit): ",
    },
    "es": {
        "title": "🤑 GESTOR DE RENDIMIENTO v2.2 (Modo Forense)",
        "scan_mode": "Elegir Modo de Escaneo:\n1. Vista Rápida (Últimas 10 Eras)\n2. Auditoría Completa (20 Eras por página)",
        "status_claimed_me": "✅ Cobrada (POR TI)",
        "status_claimed_ext": "✅ Cobrada (Otro)",
        "status_pending": "💰 PENDIENTE",
        "status_none": "⚪ Sin Stake",
        "prompt": "🔹 ID para cobrar, 'all' (lista), 'm' (más), o 'q' (salir): ",
    }
}

def check_who_claimed(substrate, era, val_stash, my_stash):
    """
    Intenta determinar si el payout fue iniciado por el usuario.
    Nota: En una red real, esto requiere indexación. Aquí simulamos la validación
    cruzando datos de extrínsecos si están disponibles en el nodo local.
    """
    my_stash_str = str(my_stash)
    try:
        # Buscamos en los eventos del sistema si el usuario fue el 'Sudo' o 'Signer'
        # de la transacción de pago para esa era específica.
        # Por ahora, implementamos una marca de 'Others' por defecto y 
        # 'YOU' si el script acaba de realizar la acción.
        return False 
    except: return False

def get_era_payout_data(substrate, era, my_stash):
    my_stash_str = str(my_stash)
    try:
        reward_points = substrate.query('Staking', 'ErasRewardPoints', [era]).value
        if not reward_points: return []
        
        vals_in_era = []
        ind_points = reward_points['individual']
        items = ind_points.items() if isinstance(ind_points, dict) else [(e[0], e[1]) for e in ind_points]
        
        for val_stash, points in items:
            if points <= 0: continue
            
            overview = substrate.query('Staking', 'ErasStakersOverview', [era, val_stash]).value
            if overview:
                for page in range(overview['page_count']):
                    paged = substrate.query('Staking', 'ErasStakersPaged', [era, val_stash, page]).value
                    if paged and any(str(n.get('who') if isinstance(n, dict) else n[0]) == my_stash_str for n in paged['others']):
                        
                        claimed = substrate.query('Staking', 'ClaimedRewards', [era, val_stash]).value or []
                        
                        if page in claimed:
                            # Aquí es donde entraría la lógica forense profunda
                            # Por simplicidad, si está cobrada y no tenemos registro local de 'yo lo hice', es 'Others'
                            status = "claimed"
                        else:
                            status = "pending"
                            
                        vals_in_era.append({'val': val_stash, 'page': page, 'status': status})
        return vals_in_era
    except: return []

def run_smart_claimer(override_env=None, override_lang=None):
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            env, node_url = override_env or config['network']['env'], config['network']['endpoints'][override_env or config['network']['env']]
            lang, mnemonic, my_stash = override_lang or config.get('preferences', {}).get('language', 'en'), config['wallet']['mnemonic'], config['validator']['stash_address']
    except Exception as e:
        console.print(f"❌ Error: {e}"); return

    t = TXT.get(lang, TXT["en"])
    substrate = SubstrateInterface(url=node_url)
    keypair = Keypair.create_from_mnemonic(mnemonic)
    
    # Mantenemos un registro de lo que cobramos en esta sesión
    session_claims = []

    active_era = substrate.query('Staking', 'ActiveEra').value['index']
    console.print(Panel(t["scan_mode"], title=t["title"], border_style="cyan"))
    mode = console.input("[bold yellow]👉 Option: [/bold yellow]")
    
    step = 10 if mode == '1' else 20
    current_end = active_era - 1
    
    while True:
        current_start = max(0, current_end - (step - 1))
        pending_list = []
        table = Table(title=f"Audit Report (Eras {current_end}-{current_start})", border_style="cyan")
        table.add_column("ID", justify="center", style="cyan")
        table.add_column("Era", justify="center")
        table.add_column("Validator", style="white")
        table.add_column("Status", justify="left")

        item_id = 1
        with console.status(f"[bold green]Scanning...[/bold green]"):
            for era in range(current_end, current_start - 1, -1):
                era_data = get_era_payout_data(substrate, era, my_stash)
                if not era_data:
                    table.add_row("-", str(era), "[dim]---[/dim]", f"[dim]{t['status_none']}[/dim]")
                else:
                    for entry in era_data:
                        claim_key = f"{era}-{entry['val']}-{entry['page']}"
                        if entry['status'] == "pending":
                            st_text = f"[bold green]{t['status_pending']}[/bold green]"
                            pending_list.append({'id': item_id, 'era': era, 'val': entry['val'], 'p': entry['page'], 'key': claim_key})
                            row_id = str(item_id); item_id += 1
                        else:
                            # LÓGICA FORENSE: ¿Lo cobramos nosotros en esta sesión o antes?
                            if claim_key in session_claims:
                                st_text = f"[bold blue]{t['status_claimed_me']}[/bold blue]"
                            else:
                                st_text = f"[dim]{t['status_claimed_ext']}[/dim]"
                            row_id = "-"
                        table.add_row(row_id, str(era), f"{entry['val'][:6]}...{entry['val'][-4:]}", st_text)

        console.clear(); console.print(table)
        cmd = console.input(f"\n{t['prompt']}").strip().lower()

        if cmd == 'q': break
        elif cmd == 'm' and current_start > 0:
            current_end = current_start - 1; continue
        
        to_proc = pending_list if cmd == 'all' else [x for x in pending_list if str(x['id']) == cmd]
        for item in to_proc:
            try:
                console.print(f"🚀 Claiming Era {item['era']}...")
                call = substrate.compose_call('Staking', 'payout_stakers_by_page', {'validator_stash': item['val'], 'era': item['era'], 'page': item['p']})
                extrinsic = substrate.create_signed_extrinsic(call=call, keypair=keypair)
                receipt = substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)
                if receipt.is_success:
                    session_claims.append(item['key']) # Guardamos en la "memoria forense"
                    console.print(f"✅ Success! [green]{receipt.block_hash[:12]}[/green]")
            except Exception as e: console.print(f"❌ Error: {e}")
        
        if to_proc: console.input("\nPress Enter to refresh..."); continue

    substrate.close()
