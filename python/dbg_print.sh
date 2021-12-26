#!/bin/bash
IF=wlan0
SCAN_COUNT=7
echo "- DEBUG -"
echo -n "WIFI: "; /usr/sbin/iwconfig $IF | head -1 | sed 's/^[^"]* ESSID:"\([^"]*\)".*/\1/'
echo -n "IP: "; /usr/sbin/ifconfig $IF | grep '^\s*inet ' | sed 's/^\s* inet \([0-9.]*\) .*/\1/'
echo -n "GW: "; /usr/sbin/route -n | grep '^0\.0\.0\.0' | sed 's/^0.0.0.0\s*\([0-9.]*\).*/\1/'
SCANRESULT=""
for ((i=0; i < 10; i=i+1)); do
  sudo iwlist wlan0 s > /tmp/wlan-scan-result
  cat /tmp/wlan-scan-result | head -1 | grep 'Scan completed' >/dev/null && break
  sleep 1
done
echo "$IF top $SCAN_COUNT:"
  ( \
    echo '';  \
    cat /tmp/wlan-scan-result \
    | egrep '^\s*ESSID:|^\s*Quality=' \
    | sed -e 's/^\s*ESSID:"\([^"]*\)".*/\1#/'  -e 's/^\s*Quality=\([0-9]*\).*/\1/' \
  ) \
  | tr '\n' ' ' \
  | tr '#' '\n' \
  | grep . \
  | sort -u \
  | sed 's/^ //' \
  | grep '^[0-9]\+ .' \
  | sort -nru \
  | head -$SCAN_COUNT \
  | sed 's/^\(.\{20\}\).*/\1/'
