#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
state_dir="$HOME/.local/share/urbanflow"
binary="$state_dir/mongodb/bin/mongod"
mkdir -p "$state_dir/mongodb" "$state_dir/mongo"
if [ ! -x "$binary" ]; then
  tar -xzf "$project_root/.tools/mongodb.tgz" -C "$state_dir/mongodb" --strip-components=1
fi
if pgrep -f "mongod --dbpath $state_dir/mongo" >/dev/null; then
  echo "UrbanFlow MongoDB is already running"
  exit 0
fi
"$binary" --dbpath "$state_dir/mongo" --bind_ip 127.0.0.1 --port 27017 \
  --logpath "$state_dir/mongod.log" --fork
