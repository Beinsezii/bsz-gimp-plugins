#!/usr/bin/bash
cd "${0%/*}"
cargo build --target x86_64-unknown-linux-gnu --release
cargo build --target x86_64-pc-windows-gnu --release
ln -sf pixelbuster/target/x86_64-unknown-linux-gnu/release/libpixelbuster.so ../pixelbuster.so
ln -sf pixelbuster/target/x86_64-pc-windows-gnu/release/pixelbuster.dll ../
strip ../pixelbuster.so ../pixelbuster.dll
