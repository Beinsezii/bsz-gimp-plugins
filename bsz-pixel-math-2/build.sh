cd "${0%/*}"
rustc --crate-type cdylib -O pixel-math-2.rs
mv libpixel_math_2.so pixel_math_2.so
strip pixel_math_2.so
rustc --crate-type cdylib -O --target x86_64-pc-windows-gnu pixel-math-2.rs
rm libpixel_math_2.dll.a
strip pixel_math_2.dll
