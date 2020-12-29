cd "${0%/*}"
rustc --crate-type cdylib -O filmic-chroma.rs
mv libfilmic_chroma.so filmic_chroma.so
strip filmic_chroma.so
rustc --crate-type cdylib -O --target x86_64-pc-windows-gnu filmic-chroma.rs
rm libfilmic_chroma.dll.a
strip filmic_chroma.dll
