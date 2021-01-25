use std::os::raw;
use std::sync::Arc;

// structs {{{
enum Op {
    Add,
    Sub,
    Mul,
    Div,
    Mod,
    Pow,
    Set,
    Abs,
    Acos,
    Acosh,
    Asin,
    Asinh,
    Atan,
    Atan2,
    Atanh,
    Cbrt,
    Ceil,
    Cos,
    Cosh,
    Floor,
    Log,
    Max,
    Min,
    Round,
    Sin,
    Sinh,
    Sqrt,
    Tan,
    Tanh,
}


enum Obj {
    Chan(usize),
    Var(usize),
    Num(f64),
    E,
    Pi,
    Rand,
}


struct Operation {
    target: Obj,
    operation: Op,
    value: Obj,
}
// }}}


fn parse_ops(mut ops: String, mut chs: String) -> Vec<Operation> {
    // {{{
    ops.make_ascii_lowercase();
    chs.make_ascii_lowercase();
    let mut line = 0;
    let mut result = Vec::<Operation>::new();
    for op in ops.trim().split('\n') {
        line += 1;
        let items = op.split_ascii_whitespace().collect::<Vec<&str>>();
        if items.len() != 3 {
            println!("Invalid number of args on operation line {}", line);
            continue
        }

        result.push( Operation{
            target: match items[0] {
                // don't hate I made these with a vim macro
                "c1" => Obj::Chan(0),
                "c2" => Obj::Chan(1),
                "c3" => Obj::Chan(2),
                "c4" => Obj::Chan(3),
                "v1" | "v" => Obj::Var(0),
                "v2" => Obj::Var(1),
                "v3" => Obj::Var(2),
                "v4" => Obj::Var(3),
                "v5" => Obj::Var(4),
                "v6" => Obj::Var(5),
                "v7" => Obj::Var(6),
                "v8" => Obj::Var(7),
                "v9" => Obj::Var(8),
                val => {
                    match chs.find(val) {
                        Some(n) => Obj::Chan(n),
                        None => {
                            println!("Invalid target on operation line {}", line);
                            continue
                        }
                    }
                },
            },

            operation: match items[1] {
                "+=" | "+" | "add" => Op::Add,
                "-=" | "-" | "sub" => Op::Sub,
                "*=" | "*" | "mul" => Op::Mul,
                "/=" | "/" | "div" => Op::Div,
                "%=" | "%" | "mod" => Op::Mod,
                "**" | "^" | "pow" => Op::Pow,
                "=" | "set" => Op::Set,
                "abs" => Op::Abs,
                "acos" => Op::Acos,
                "acosh" => Op::Acosh,
                "asin" => Op::Asin,
                "asinh" => Op::Asinh,
                "atan" => Op::Atan,
                "atan2" => Op::Atan2,
                "atanh" => Op::Atanh,
                "cbrt" => Op::Cbrt,
                "ceil" => Op::Ceil,
                "cos" => Op::Cos,
                "cosh" => Op::Cosh,
                "floor" => Op::Floor,
                "log" => Op::Log,
                "max" => Op::Max,
                "min" => Op::Min,
                "round" => Op::Round,
                "sin" => Op::Sin,
                "sinh" => Op::Sinh,
                "sqrt" => Op::Sqrt,
                "tan" => Op::Tan,
                "tanh" => Op::Tanh,
                _ => {
                    println!("Invalid math operator on operation line {}", line);
                    continue
                },
            },

            value: match items[2] {
                "c1" => Obj::Chan(0),
                "c2" => Obj::Chan(1),
                "c3" => Obj::Chan(2),
                "c4" => Obj::Chan(3),
                "v1" | "v" => Obj::Var(0),
                "v2" => Obj::Var(1),
                "v3" => Obj::Var(2),
                "v4" => Obj::Var(3),
                "v5" => Obj::Var(4),
                "v6" => Obj::Var(5),
                "v7" => Obj::Var(6),
                "v8" => Obj::Var(7),
                "v9" => Obj::Var(8),
                "e" => Obj::E,
                "pi" => Obj::Pi,
                "rand" => Obj::Rand,
                val => {
                    match chs.find(val) {
                        Some(n) => Obj::Chan(n),
                        None => {
                            match val.parse::<f64>() {
                                Ok(n) => Obj::Num(n),
                                Err(_) => {   // yeah so it's a pyramid
                                    println!("Invalid value on operation line {}", line);
                                    continue
                                }
                            }
                        }
                    }
                },
            }
        });

    }

    result
} // }}}


fn process_segment(ops: &Vec<Operation>, pixels: &mut [f64]) {
    // {{{
    assert!(pixels.len() % 4 == 0);

    let mut vars = 0;
    for op in ops {
        match op.value {
            Obj::Var(i) => vars = std::cmp::max(vars, i+1),
            _ => (),
        }
        match op.value {
            Obj::Var(i) => vars = std::cmp::max(vars, i+1),
            _ => (),
        }
    }

    let mut v = [0.0_f64; 9];

    for pixel in pixels.chunks_mut(4) {
        for op in ops.iter() {
            let val: f64 = match op.value {
                Obj::Chan(i) => pixel[i],
                Obj::Var(i) => v[i],
                Obj::Num(n) => n,
                Obj::E => std::f64::consts::E,
                Obj::Pi => std::f64::consts::PI,
                Obj::Rand => rand::random::<f64>(),
            };

            let tar: &mut f64 = match op.target {
                Obj::Chan(i) => &mut pixel[i],
                Obj::Var(i) => &mut v[i],
                _ => panic!("This shouldn't be reachable"),
            };

            match op.operation {
                Op::Add => *tar += val,
                Op::Sub => *tar -= val,
                Op::Mul => *tar *= val,
                Op::Div => *tar /= val,
                Op::Mod => *tar %= val,
                Op::Pow => *tar = tar.powf(val),
                Op::Set => *tar = val,
                Op::Abs => *tar = val.abs(),
                Op::Acos => *tar = val.acos(),
                Op::Acosh => *tar = val.acosh(),
                Op::Asin => *tar = val.asin(),
                Op::Asinh => *tar = val.asinh(),
                Op::Atan => *tar = val.atan(),
                Op::Atan2 => *tar = tar.atan2(val),
                Op::Atanh => *tar = val.atanh(),
                Op::Cbrt => *tar = val.cbrt(),
                Op::Ceil => *tar = val.ceil(),
                Op::Cos => *tar = val.cos(),
                Op::Cosh => *tar = val.cosh(),
                Op::Floor => *tar = val.floor(),
                Op::Log => *tar = tar.log(val),
                Op::Max => *tar = tar.max(val),
                Op::Min => *tar = tar.min(val),
                Op::Round => *tar = val.round(),
                Op::Sin => *tar = val.sin(),
                Op::Sinh => *tar = val.sinh(),
                Op::Sqrt => *tar = val.sqrt(),
                Op::Tan => *tar = val.tan(),
                Op::Tanh => *tar = val.tanh(),
            };
        }
    };
} // }}}


#[no_mangle]
pub extern "C" fn pixelbuster(
    // {{{
    code: *const raw::c_char,
    channels: *const raw::c_char,
    pixels: *mut raw::c_char,
    len: usize) {

    let len = len/8;

    let code = unsafe {
        assert!(!code.is_null());
        std::ffi::CStr::from_ptr(code).to_str().expect("Invalid code string").to_string()
    };
    let channels = unsafe {
        assert!(!channels.is_null());
        std::ffi::CStr::from_ptr(channels).to_str().expect("Invalid channels string").to_string()
    };
    let pixels = unsafe {
        assert!(!pixels.is_null());
        std::slice::from_raw_parts_mut(pixels.cast::<f64>(), len)
    };

    let ops = Arc::new(parse_ops(code, channels));

    let mut threads = Vec::new();

    let count: usize = num_cpus::get();
    let mut chunks: Vec<&mut[f64]> = pixels.chunks_mut((len/4)/count*4).collect();

    for _ in 0..chunks.len() {
        let chunk: &mut [f64] = chunks.pop().unwrap();
        let op = ops.clone();
        threads.push(std::thread::spawn(move || process_segment(&op, chunk)));
    }

    for t in threads {
        t.join().expect("Thread fail");
    }
} // }}}
