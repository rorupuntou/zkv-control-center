
# 🚀 zkVerify Validator Control Center v1.1
**By roru1312 | Uruguay Command Center 🇺🇾**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Substrate](https://img.shields.io/badge/Substrate-Ready-green.svg)](https://substrate.io/)

A comprehensive, bilingual (EN/ES) CLI suite designed for zkVerify node operators. Monitor consensus, audit staking, claim rewards, and manage your on-chain identity and security posture through a single, secure interface.


## ✨ Features
- **🛡️ Advanced Sentinel:** Real-time monitoring of Peers, Blocks, and Mempool.
- **💰 Auto-Payout Auditor:** Hybrid scanning for pending rewards with "Claim All" functionality.
- **📡 Paged Radar:** Deep audit of Paged Staking and Nominator distributions.
- **🏛️ Governance Auditor:** Decode OpenGov referenda preimages and track voting tallies.
- **🆔 Identity Manager:** Set your on-chain display name securely.
- **⚙️ Configuration Manager:** Interactive, first-time setup for your Mnemonic and Stash addresses.
- **🔒 DeepSec Net Auditor (NEW):** OPSEC tool to scan local firewall rules, exposed ports (RPC/Metrics), and active P2P connections to prevent critical leaks.
- **🤑 Smart Yield Claimer (NEW):** Forensic mode payout scanner to track historical claims and automatically process pending rewards by era and page.

## 🛠️ Quick Installation
Compatible with Linux and macOS. The installer uses a Python Virtual Environment (`venv`) to ensure a clean, isolated setup.

```bash
git clone https://github.com/rorupuntou/zkv-control-center.git
cd zkv-control-center
bash install.sh
source venv/bin/activate
python main.py

```

## 🔐 Security First

* **Local Processing:** Your mnemonic is processed locally and never leaves your machine.
* **Isolated Environment:** Dependencies are installed in a dedicated venv to prevent OS conflicts.
* **Configuration:** All sensitive data is stored in `config.yaml`, which is automatically ignored by Git.
* **Log Management:** Security audits and local logs are strictly `.gitignore`d to prevent accidental doxxing of your node's IP.

## 🌍 Language & Environment

Switch between English/Spanish and Local/Volta/Mainnet directly from the main menu without editing any code.

---

## 🤝 Support & Development

Built from the South. Support the Uruguayan Validator Node. Let's build a more transparent zkVerify together.

**Looking for custom Web3 infrastructure automation?**
If you need custom Python scripts, node setups, or monitoring tools for your Substrate/EVM network, feel free to reach out via GitHub issues or Telegram.
