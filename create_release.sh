#!/usr/bin/bash

printf -v date '%(%Y-%m-%d)T'

cd ./bsz-shared
cargo build --release
cd ..
strip ./bsz_shared.so

zip -q bsz-gimp-plugins_${date}.zip \
    bsz_gimp_lib.py \
    bszgw.py \
    bsz_shared.so \
    bsz-*/*.py

git tag ${date}
