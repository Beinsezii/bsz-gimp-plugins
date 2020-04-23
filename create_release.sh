#!/usr/bin/bash

printf -v date '%(%Y-%m-%d)T'

tar -cahf bsz-gimp-plugins_${date}.tar \
    bsz-dualbloom/bsz-dualbloom.py \
    bsz_gimp_lib.py \
    bszgw.py

git tag ${date}
