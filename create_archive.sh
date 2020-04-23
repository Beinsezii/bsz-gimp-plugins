#!/usr/bin/bash

tar -cahf bsz-gimp-plugins_$(printf '%(%Y-%m-%d)T').tar \
    bsz-dualbloom/bsz-dualbloom.py \
    bsz_gimp_lib.py \
    bszgw.py
