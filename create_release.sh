#!/usr/bin/bash

printf -v date '%(%Y-%m-%d)T'

tar -cahf bsz-gimp-plugins_${date}.tar \
    bsz_gimp_lib.py \
    bszgw.py \
    bsz-dualbloom/bsz-dualbloom.py \
    bsz-dualbloom2/bsz-dualbloom2.py \

git tag ${date}
