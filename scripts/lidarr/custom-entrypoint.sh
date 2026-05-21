#!/bin/sh
set -e

echo "Running post-setup for lidarr..."
/post-setup.sh

echo "Starting original process..."
exec "$@"
