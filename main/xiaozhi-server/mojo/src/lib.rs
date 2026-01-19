use libc::{c_float, c_int, c_short, c_uchar};
use opus::{Application, Channels, Decoder, Encoder};

// Rust FFI 实现（Opus/PCM/VAD），保持与 Mojo 兼容的 C ABI

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

/// 批量解码：解码多个 Opus 帧到连续 PCM。
/// in_ptr 指向拼接的所有帧；in_lens 为每帧长度数组；offsets 为每帧写入的目标样本起点（按声道展开后的样本计数）。
/// 返回写入的样本总数（含多声道），或负值错误码。
#[no_mangle]
pub extern "C" fn opus_decode_batch(
    in_ptr: *const c_uchar,
    in_lens: *const c_int,
    frames: c_int,
    sample_rate: c_int,
    channels: c_int,
    out_ptr: *mut c_short,
    out_len: c_int,
    offsets: *const c_int,
) -> c_int {
    if in_ptr.is_null()
        || in_lens.is_null()
        || out_ptr.is_null()
        || offsets.is_null()
        || frames <= 0
        || out_len <= 0
    {
        return -2;
    }
    let chan = match channels {
        1 => Channels::Mono,
        2 => Channels::Stereo,
        _ => return -3,
    };
    let sr = if sample_rate <= 0 { 16000 } else { sample_rate };
    let mut decoder = match Decoder::new(sr as u32, chan) {
        Ok(d) => d,
        Err(_) => return -4,
    };

    let lens = unsafe { std::slice::from_raw_parts(in_lens, frames as usize) };
    let offs = unsafe { std::slice::from_raw_parts(offsets, frames as usize) };
    let out_buf = unsafe { std::slice::from_raw_parts_mut(out_ptr, out_len as usize) };

    let mut cursor: usize = 0;
    let mut total_written: usize = 0;
    for (idx, &len) in lens.iter().enumerate() {
        if len <= 0 {
            continue;
        }
        let offset_samples = offs.get(idx).cloned().unwrap_or(0);
        let target = offset_samples as usize;
        if target >= out_buf.len() {
            return -5;
        }
        let input = unsafe { std::slice::from_raw_parts(in_ptr.add(cursor), len as usize) };
        let target_slice = &mut out_buf[target..];
        match decoder.decode(input, target_slice, false) {
            Ok(written) => {
                let w = written as usize * channels as usize;
                total_written = total_written.max(target + w);
            }
            Err(_) => return -1,
        }
        cursor += len as usize;
    }
    total_written as c_int
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

/// Opus 编码：将 PCM(i16) 编码为 Opus，比特流写入 out_ptr。
/// 返回写入的字节数，或负值表示错误。
#[no_mangle]
pub extern "C" fn opus_encode(
    in_ptr: *const c_short,
    in_len: c_int, // samples count (not bytes)
    sample_rate: c_int,
    channels: c_int,
    out_ptr: *mut c_uchar,
    out_len: c_int,
) -> c_int {
    if in_ptr.is_null() || out_ptr.is_null() || in_len <= 0 || out_len <= 0 {
        return -2;
    }
    let chan = match channels {
        1 => Channels::Mono,
        2 => Channels::Stereo,
        _ => return -3,
    };
    let sr = if sample_rate <= 0 { 16000 } else { sample_rate };
    let mut encoder = match Encoder::new(sr as u32, chan, Application::Audio) {
        Ok(e) => e,
        Err(_) => return -4,
    };

    let input = unsafe { std::slice::from_raw_parts(in_ptr, in_len as usize) };
    let frame_size = in_len / channels;
    if frame_size <= 0 {
        return -2;
    }
    let output = unsafe { std::slice::from_raw_parts_mut(out_ptr, out_len as usize) };
    match encoder.encode(input, output) {
        Ok(len) => len as c_int,
        Err(_) => -1,
    }
}
