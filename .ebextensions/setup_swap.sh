#!/bin/bash

SWAPDIR=/var/cache/swap
SWAPFILE=$SWAPDIR/swap0
SWAP_MEGABYTES=512

if [ -f $SWAPFILE ]; then
	echo "Swapfile $SWAPFILE found, assuming already setup"
	exit;
fi

mkdir -p $SWAPDIR
sudo dd if=/dev/zero of=$SWAPFILE bs=1M count=$SWAP_MEGABYTES
sudo chmod 0600 $SWAPFILE
sudo mkswap $SWAPFILE
sudo swapon $SWAPFILE
