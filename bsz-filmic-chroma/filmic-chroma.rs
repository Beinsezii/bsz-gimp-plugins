use std::convert::TryInto;
use std::os::raw;

#[no_mangle]
pub extern "C" fn filmic_chroma(
    scale: f64,
    offset: f64,
    invert: bool,
    bytes: *mut raw::c_char,
    len: usize) {
    let pixels = unsafe {
        std::slice::from_raw_parts_mut(bytes.cast::<u8>(), len)
    };
    for chunk in pixels.chunks_exact_mut(32) {
        let l = f64::from_le_bytes(chunk[0..8].try_into().expect("bytefail"));
        let c = f64::from_le_bytes(chunk[8..16].try_into().expect("bytefail2"));

        let c = match invert {
            false => c * (offset - l / scale),
            true => c * (offset - (100.0 - l) / scale)
        }.to_le_bytes();

        for x in 0..8 {
            chunk[x+8] = c[x];
        };
    }
}
