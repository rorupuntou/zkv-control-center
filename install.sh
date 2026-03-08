#!/bin/bash

echo "========================================================="
echo " 🛠️  Installing zkVerify Validator Control Center v1.0"
echo "========================================================="

# 1. Crear entorno virtual para evitar conflictos con el OS
echo "🌐 Creating Python Virtual Environment (venv)..."
# Usamos python3 por defecto
PYTHON_CMD="python3"

# Verificamos si python3-venv está instalado (típico en Ubuntu/Debian)
if ! $PYTHON_CMD -m venv venv 2>/dev/null; then
    echo "⚠️ Python venv module not found."
    echo "If you are on Debian/Ubuntu, please run: sudo apt install python3-venv"
    echo "Then run this script again."
    exit 1
fi

# 2. Instalar dependencias dentro del entorno virtual
echo "📦 Installing Python libraries into venv..."
./venv/bin/python3 -m pip install --upgrade pip
./venv/bin/python3 -m pip install substrate-interface pyyaml

# 3. Crear el config.yaml si no existe (Plantilla segura y en blanco)
if [ ! -f "config.yaml" ]; then
    echo "📝 Creating safe config.yaml template..."
    cat <<EOF > config.yaml
preferences:
  language: "en"

network:
  env: "local"
  endpoints:
    local: "ws://127.0.0.1:9944"
    volta: "wss://zkverify-volta-rpc.zkverify.io"
    mainnet: "wss://zkverify-rpc.zkverify.io"

wallet:
  mnemonic: ""
  address: ""

validator:
  stash_address: ""

modules:
  sentinel:
    check_interval_seconds: 10
EOF
    echo "✅ Template created successfully."
fi

# 4. Crear un script lanzador (launcher) súper amigable
echo "🚀 Creating start.sh launcher..."
cat <<EOF > start.sh
#!/bin/bash
./venv/bin/python3 main.py
EOF

# Dar permisos de ejecución
chmod +x start.sh
chmod +x main.py

echo "========================================================="
echo "🎉 INSTALLATION COMPLETE!"
echo "========================================================="
echo "👉 You can now start the application by running:"
echo "   ./start.sh"
echo ""
echo "💡 Tip: Use Option 7 in the menu to set up your wallet"
echo "   and node addresses safely."
echo "========================================================="
