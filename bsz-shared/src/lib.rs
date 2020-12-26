use pyo3::prelude::*;
use pyo3::wrap_pyfunction;
use pyo3::types::PyByteArray;
use std::convert::TryInto;

#[pyfunction]
/// Formats the sum of two numbers as string.
fn filmic_chroma(scale: f64, offset: f64, invert: bool, bytes: &PyByteArray) {
    unsafe {
        for chunk in bytes.as_bytes_mut().chunks_exact_mut(32) {
            let l = f64::from_le_bytes(chunk[0..8].try_into().expect("bytefail"));
            let mut c: f64 = f64::from_le_bytes(chunk[8..16].try_into().expect("bytefail2"));

            c *= offset - match invert {
            false => l / scale,
            true => (100.0 - l) / scale,
            };

            let c = c.to_le_bytes();

            for x in 0..8 {
                chunk[x+8] = c[x];
            };
        }
    }
}

#[pymodule]
/// A Python module implemented in Rust.
fn bsz_shared(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(filmic_chroma, m)?)?;

    Ok(())
}
