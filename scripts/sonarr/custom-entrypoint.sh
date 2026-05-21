#!/bin/sh
set -e

echo "Running post-setup for sonarr..."
/post-setup.sh

echo "Starting original process..."
exec "$@"
