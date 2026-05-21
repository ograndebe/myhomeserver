#!/bin/sh
set -e

echo "Running post-setup for prowlarr..."
/post-setup.sh

echo "Starting original process..."
exec "$@"
