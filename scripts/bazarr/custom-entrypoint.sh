#!/bin/sh
set -e

echo "Running post-setup for bazarr..."
/post-setup.sh

echo "Starting original process..."
exec "$@"
