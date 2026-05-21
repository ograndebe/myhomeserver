#!/bin/sh
set -e

echo "Running post-setup for qbittorrent..."
/post-setup.sh

echo "Starting original process..."
exec "$@"
