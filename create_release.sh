#!/usr/bin/bash

printf -v date '%(%Y-%m-%d)T'

zip -q bsz-gimp-plugins_${date}.zip \
    bsz_gimp_lib.py \
    bszgw.py \
    bsz-*/*.py

git tag ${date}
