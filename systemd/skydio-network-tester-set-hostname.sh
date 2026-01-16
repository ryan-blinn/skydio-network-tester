#!/bin/bash

set -e

current="$(hostname)"

marker="/etc/skydio-network-tester-hostname-set"

if [ -f "$marker" ]; then
  exit 0
fi

is_default=0
case "${current,,}" in
  ""|"raspberrypi"|"localhost"|raspberrypi*) is_default=1 ;;
  skydiont-*) is_default=0 ;;
  skydio-nt*|skydiont*|skydio-network-tester*) is_default=1 ;;
  *) is_default=0 ;;
esac

if [ "$is_default" -ne 1 ]; then
  exit 0
fi

mac=""

for _ in 1 2 3 4 5; do
  for iface in eth0 wlan0; do
    if [ -r "/sys/class/net/$iface/address" ]; then
      m="$(cat "/sys/class/net/$iface/address" | tr '[:upper:]' '[:lower:]' | tr -d '\n' || true)"
      if [ -n "$m" ] && [ "$m" != "00:00:00:00:00:00" ]; then
        mac="$m"
        break
      fi
    fi
  done
  if [ -n "$mac" ]; then
    break
  fi
  sleep 1
done

if [ -z "$mac" ]; then
  for p in /sys/class/net/*/address; do
    iface="$(basename "$(dirname "$p")")"
    if [ "$iface" = "lo" ]; then
      continue
    fi
    m="$(cat "$p" 2>/dev/null | tr '[:upper:]' '[:lower:]' | tr -d '\n' || true)"
    if [ -n "$m" ] && [ "$m" != "00:00:00:00:00:00" ]; then
      mac="$m"
      break
    fi
  done
fi

hex="$(echo "$mac" | tr -cd '0-9a-f')"
suffix="${hex: -4}"
if [ -z "$suffix" ]; then
  suffix="0000"
fi
suffix="${suffix^^}"
new_name="SkydioNT-$suffix"

hostnamectl set-hostname "$new_name"

if [ -w /etc/hosts ]; then
  if grep -qE '^[[:space:]]*127\.0\.1\.1[[:space:]]+' /etc/hosts; then
    sed -i -E "s/^[[:space:]]*127\\.0\\.1\\.1[[:space:]]+.*/127.0.1.1\t$new_name/" /etc/hosts
  else
    printf "127.0.1.1\t%s\n" "$new_name" >> /etc/hosts
  fi
fi

touch "$marker"
