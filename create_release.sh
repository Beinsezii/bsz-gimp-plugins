#!/usr/bin/bash

printf -v date '%(%Y-%m-%d)T'

bsz-*/build.sh

zip -q bsz-gimp-plugins_${date}.zip \
    bsz_gimp_lib.py \
    bszgw.py \
    bsz-*/*.py \
    bsz-*/*.dll \
    bsz-*/*.so

git tag ${date}
