#!/bin/sh
# Build dist/WakaTime.zip; with --install also add it to calibre (close calibre first).
set -e
cd "$(dirname "$0")"
mkdir -p dist
rm -f dist/WakaTime.zip
(cd plugin && zip -qr ../dist/WakaTime.zip . -x '*.pyc' -x '__pycache__/*' -x '.DS_Store')
echo "built dist/WakaTime.zip"
[ "$1" = "--install" ] && calibre-customize -a dist/WakaTime.zip
exit 0
