#!/bin/bash

# Script para construir las dos imágenes Docker del bot
# Uso: ./build_images.sh

set -e

echo "🔨 Construyendo imágenes Docker para los bots de trading..."
echo ""

# Directorio donde está el código del bot
BOT_DIR="."

# Verificar que existe Dockerfile
if [ ! -f "$BOT_DIR/Dockerfile" ]; then
    echo "❌ Error: No se encuentra Dockerfile en $BOT_DIR"
    exit 1
fi

echo "📦 Construyendo imagen para ETH bot..."
docker build -t bot_trading_ia-eth-ai:latest "$BOT_DIR"

if [ $? -eq 0 ]; then
    echo "✅ Imagen bot_trading_ia-eth-ai:latest construida exitosamente"
else
    echo "❌ Error al construir imagen ETH"
    exit 1
fi

echo ""
echo "📦 Construyendo imagen para BTC bot..."
docker build -t bot_trading_ia-btc-ai:latest "$BOT_DIR"

if [ $? -eq 0 ]; then
    echo "✅ Imagen bot_trading_ia-btc-ai:latest construida exitosamente"
else
    echo "❌ Error al construir imagen BTC"
    exit 1
fi

echo ""
echo "🎉 Ambas imágenes construidas exitosamente!"
echo ""
echo "📋 Imágenes disponibles:"
docker images | grep "bot_trading_ia"

echo ""
echo "✅ Listo! Ahora puedes iniciar la API y los contenedores se levantarán automáticamente al guardar las configuraciones."
