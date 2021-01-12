use std::os::raw;

#[no_mangle]
pub extern "C" fn filmic_chroma(
    scale: f64,
    offset: f64,
    invert: bool,
    bytes: *mut raw::c_char,
    len: usize) {
    let pixels = unsafe {
        std::slice::from_raw_parts_mut(bytes.cast::<f64>(), len/8)
    };
    for pixel in pixels.chunks_exact_mut(4) {
        pixel[1] = match invert {
            false => pixel[1] * (offset - pixel[0] / scale),
            true => pixel[1] * (offset - (100.0 - pixel[0]) / scale)
        };
    };
}
