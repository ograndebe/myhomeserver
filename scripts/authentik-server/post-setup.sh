#!/bin/sh
set -e

echo "[authentik-post-setup] Iniciando post-setup..."
python3 /post-setup.py

echo "[authentik-post-setup] Concluído."
