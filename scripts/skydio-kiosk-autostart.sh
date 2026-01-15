#!/bin/bash

set -e

detected=0

for _i in $(seq 1 30); do
  for _vs in /sys/class/graphics/fb*/virtual_size; do
    [ -r "${_vs}" ] || continue
    _val="$(cat "${_vs}" 2>/dev/null || true)"
    case "${_val}" in
      480,320|320,480) detected=1 ;;
    esac
  done

  if [ "${detected}" -eq 1 ]; then
    break
  fi

  sleep 1
done

if [ "${detected}" -eq 1 ]; then
  systemctl start skydio-network-tester.service || true
  systemctl start lightdm.service || true
fi
