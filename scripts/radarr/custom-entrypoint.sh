#!/bin/sh
set -e

echo "Running post-setup for radarr..."
/post-setup.sh

echo "Starting original process..."
exec "$@"
