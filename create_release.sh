#!/usr/bin/bash
cd "${0%/*}"

printf -v date '%(%Y-%m-%d)T'

bsz-*/build.sh
pixelbuster/build.sh

zip -q bsz-gimp-plugins_${date}.zip \
    bsz_gimp_lib.py \
    bszgw.py \
    libpixelbuster.so \
    pixelbuster.dll \
    bsz-*/bsz-*.py \
    bsz-*/*.dll \
    bsz-*/*.so

git tag ${date}
