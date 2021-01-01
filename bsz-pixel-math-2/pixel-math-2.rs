use std::convert::TryInto;
use std::os::raw;


#[derive(Clone, Copy)]
enum Op {
    Add,
    Sub,
    Mul,
    Div,
    Set,
}


#[derive(Clone, Copy)]
enum Obj {
    Chan(usize),
    Var(usize),
    Num(f64),
}


#[derive(Clone, Copy)]
struct Operation {
    target: Obj,
    operation: Op,
    value: Obj,
}


fn parse_ops(ops: &str) -> Vec<Operation> {
    let mut line = 0;
    let mut result = Vec::<Operation>::new();
    for op in ops.trim().to_ascii_lowercase().split('\n') {
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
                "v1" => Obj::Var(0),
                "v2" => Obj::Var(1),
                "v3" => Obj::Var(2),
                "v4" => Obj::Var(3),
                "v5" => Obj::Var(4),
                "v6" => Obj::Var(5),
                "v7" => Obj::Var(6),
                "v8" => Obj::Var(7),
                "v9" => Obj::Var(8),
                _ => {
                    println!("Invalid target on operation line {}", line);
                    continue
                },
            },

            operation: match items[1] {
                "+=" | "+" => Op::Add,
                "-=" | "-" => Op::Sub,
                "*=" | "*" => Op::Mul,
                "/=" | "/" => Op::Div,
                "==" | "=" => Op::Set,
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
                "v1" => Obj::Var(0),
                "v2" => Obj::Var(1),
                "v3" => Obj::Var(2),
                "v4" => Obj::Var(3),
                "v5" => Obj::Var(4),
                "v6" => Obj::Var(5),
                "v7" => Obj::Var(6),
                "v8" => Obj::Var(7),
                "v9" => Obj::Var(8),
                s => {
                    match s.parse::<f64>() {
                        Ok(n) => Obj::Num(n),
                        Err(_) => {
                            println!("Invalid value on operation line {}", line);
                            continue
                        }
                    }
                },
            }
        });

    }

    result
}


#[no_mangle]
pub extern "C" fn pixel_math_2(
    code: *const raw::c_char,
    pixels: *mut raw::c_char,
    len: usize) {

    let code = unsafe {
        assert!(!code.is_null());
        std::ffi::CStr::from_ptr(code).to_str().expect("Invalid code string")
    };
    let pixels = unsafe {
        assert!(!pixels.is_null());
        std::slice::from_raw_parts_mut(pixels.cast::<u8>(), len)
    };

    let ops = parse_ops(code);

    for chunk in pixels.chunks_exact_mut(32) {
        let mut c: [f64; 4] = [
            f64::from_le_bytes(chunk[0..8].try_into().expect("bytefail c1")),
            f64::from_le_bytes(chunk[8..16].try_into().expect("bytefail c2")),
            f64::from_le_bytes(chunk[16..24].try_into().expect("bytefail c3")),
            f64::from_le_bytes(chunk[24..32].try_into().expect("bytefail c4")),
        ];
        let mut v: [f64; 9] = [0.0; 9];

        for op in ops.iter() {
            let val: f64 = match op.value {
                Obj::Chan(i) => c[i],
                Obj::Var(i) => v[i],
                Obj::Num(n) => n,
            };
            let tar: &mut f64 = match op.target {
                Obj::Chan(i) => &mut c[i],
                Obj::Var(i) => &mut v[i],
                Obj::Num(_) => panic!("This shouldn't be reachable"),
            };
            match op.operation {
                Op::Add => *tar += val,
                Op::Sub => *tar -= val,
                Op::Mul => *tar *= val,
                Op::Div => *tar /= val,
                Op::Set => *tar = val,
            };
        }

        let c1b = c[0].to_le_bytes();
        let c2b = c[1].to_le_bytes();
        let c3b = c[2].to_le_bytes();
        let c4b = c[3].to_le_bytes();
        for x in 0..8 {chunk[x] = c1b[x]};
        for x in 0..8 {chunk[x+8] = c2b[x]};
        for x in 0..8 {chunk[x+16] = c3b[x]};
        for x in 0..8 {chunk[x+24] = c4b[x]};
    };
}
