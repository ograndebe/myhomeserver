#!/bin/sh
set -e

echo "Running post-setup for authentik-server..."
/post-setup.sh

echo "Starting original process..."
exec dumb-init -- ak "$@"
