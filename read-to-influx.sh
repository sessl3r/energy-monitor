#!/bin/bash

if [ $# -ne 2 ]; then
	echo "Usage: $0 <device> <measurement>"
	exit 1
fi

DEVICE=$1
MEASURE=$2

stty -F $DEVICE 115200 raw -clocal -echo icrnl min 1

while read TEMP; do
	[ -z $TEMP ] && continue
	P1=$(echo $TEMP | cut -d',' -f1)
	P1=$(echo "$P1-20" | bc)
	P2=$(echo $TEMP | cut -d',' -f2)
	P2=$(echo "$P2-20" | bc)
	P3=$(echo $TEMP | cut -d',' -f3 | tr -d $'\r')
	P3=$(echo "$P3-20" | bc)
	curl -XPOST "http://localhost:8086/write?db=openhab" \
		--header "Authorization: Token openhab:openhab" \
		--data-binary "$MEASURE l1=${P1},l2=${P2},l3=${P3}" &>/dev/null
done < $DEVICE

