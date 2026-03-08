import yaml
import os

TXT = {
    "en": {
        "title": "⚙️  CONTROL CENTER CONFIGURATION",
        "current_mne": "Current Mnemonic: {status}",
        "current_addr": "Current Address: {addr}",
        "set": "[SET]", "unset": "[EMPTY]",
        "prompt_mne": "🔑 Enter new Mnemonic (Seed Phrase): ",
        "prompt_addr": "💳 Enter your Public Address: ",
        "prompt_stash": "🏦 Enter Validator Stash Address: ",
        "success": "✅ Configuration updated successfully!",
        "menu_q": "q. Return to main menu"
    },
    "es": {
        "title": "⚙️  CONFIGURACIÓN DEL CONTROL CENTER",
        "current_mne": "Mnemónico actual: {status}",
        "current_addr": "Dirección actual: {addr}",
        "set": "[CONFIGURADO]", "unset": "[VACÍO]",
        "prompt_mne": "🔑 Ingresa el nuevo Mnemónico (Seed Phrase): ",
        "prompt_addr": "💳 Ingresa tu Dirección Pública: ",
        "prompt_stash": "🏦 Ingresa la Dirección Stash del Validador: ",
        "success": "✅ ¡Configuración actualizada con éxito!",
        "menu_q": "q. Volver al menú principal"
    }
}

def run_config_manager(override_lang=None):
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
    except Exception as e:
        print(f"❌ Error: {e}"); return

    lang = override_lang if override_lang else config.get('preferences', {}).get('language', 'en')
    t = TXT[lang]

    print("\n" + "="*55 + f"\n {t['title']}\n" + "="*55)
    
    mne_status = t["set"] if config['wallet'].get('mnemonic') else t["unset"]
    addr_status = config['wallet'].get('address') if config['wallet'].get('address') else t["unset"]
    
    print(t["current_mne"].format(status=mne_status))
    print(t["current_addr"].format(addr=addr_status))
    print("-" * 55)

    new_mne = input(t["prompt_mne"]).strip()
    if new_mne: config['wallet']['mnemonic'] = new_mne

    new_addr = input(t["prompt_addr"]).strip()
    if new_addr: config['wallet']['address'] = new_addr

    new_stash = input(t["prompt_stash"]).strip()
    if new_stash: config['validator']['stash_address'] = new_stash

    with open(config_path, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)
    
    print(f"\n{t['success']}")
    input("\nPress Enter to return...")
