use libc::{c_float, c_int, c_short, c_uchar};

// 简单占位实现：复制或计算能量，后续可替换为 Mojo/FFI 绑定

/// Opus 解码占位：目前不解码，直接返回错误码 -1
#[no_mangle]
pub extern "C" fn opus_decode(
    _in_ptr: *const c_uchar,
    _in_len: c_int,
    _sample_rate: c_int,
    _channels: c_int,
    _out_ptr: *mut c_short,
    _out_len: c_int,
) -> c_int {
    // TODO: 绑定 libopus，写入 out_ptr，返回写入样本数
    -1
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
