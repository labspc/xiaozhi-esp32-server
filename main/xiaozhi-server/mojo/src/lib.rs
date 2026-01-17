use libc::{c_float, c_int, c_short, c_uchar};
use opus::Decoder;

// 简单占位实现：复制或计算能量，后续可替换为 Mojo/FFI 绑定

/// Opus 解码占位：目前不解码，直接返回错误码 -1
#[no_mangle]
pub extern "C" fn opus_decode(
    in_ptr: *const c_uchar,
    in_len: c_int,
    sample_rate: c_int,
    channels: c_int,
    out_ptr: *mut c_short,
    out_len: c_int,
) -> c_int {
    if in_ptr.is_null() || out_ptr.is_null() || in_len <= 0 || out_len <= 0 {
        return -2;
    }
    let chan = match channels {
        1 => opus::Channels::Mono,
        2 => opus::Channels::Stereo,
        _ => return -3,
    };
    let sr = if sample_rate <= 0 { 16000 } else { sample_rate };
    let mut decoder = match Decoder::new(sr as u32, chan) {
        Ok(d) => d,
        Err(_) => return -4,
    };

    let input = unsafe { std::slice::from_raw_parts(in_ptr, in_len as usize) };
    let output = unsafe { std::slice::from_raw_parts_mut(out_ptr, out_len as usize) };
    match decoder.decode(input, output, false) {
        Ok(len) => len as c_int, // 返回样本数
        Err(_) => -1,
    }
}

/// PCM int16 -> float32，占位为简单转换
#[no_mangle]
pub extern "C" fn pcm_to_float(
    in_ptr: *const c_short,
    len: c_int,
    out_ptr: *mut c_float,
) -> c_int {
    if in_ptr.is_null() || out_ptr.is_null() || len <= 0 {
        return -2;
    }
    let len_usize = len as usize;
    let input = unsafe { std::slice::from_raw_parts(in_ptr, len_usize) };
    let output = unsafe { std::slice::from_raw_parts_mut(out_ptr, len_usize) };
    for (i, &v) in input.iter().enumerate() {
        output[i] = v as f32 / 32768.0;
    }
    len
}

/// 简单能量计算，占位
#[no_mangle]
pub extern "C" fn vad_energy(in_ptr: *const c_float, len: c_int) -> c_float {
    if in_ptr.is_null() || len <= 0 {
        return 0.0;
    }
    let len_usize = len as usize;
    let input = unsafe { std::slice::from_raw_parts(in_ptr, len_usize) };
    input.iter().map(|v| v * v).sum()
}
