#!/usr/bin/env python3

import argparse
import os
import numpy as np
import cv2

BAYER_MAP = {
    "BGGR": cv2.COLOR_BayerBG2BGR,
    "RGGB": cv2.COLOR_BayerRG2BGR,
    "GRBG": cv2.COLOR_BayerGR2BGR,
    "GBRG": cv2.COLOR_BayerGB2BGR,
}


def unpack_raw10(chunk: bytes, h: int, w: int) -> np.ndarray:
    
    # Unpack RAW10 bytes to a H×W array of uint16
    b = np.frombuffer(chunk, dtype=np.uint8)
    b = b.reshape(-1, 5)

    # Extract 4 pixels per 5 bytes
    p0 = (b[:, 0].astype(np.uint16) << 2) | ((b[:, 4] >> 0) & 0b00000011)
    p1 = (b[:, 1].astype(np.uint16) << 2) | ((b[:, 4] >> 2) & 0b00000011)
    p2 = (b[:, 2].astype(np.uint16) << 2) | ((b[:, 4] >> 4) & 0b00000011)
    p3 = (b[:, 3].astype(np.uint16) << 2) | ((b[:, 4] >> 6) & 0b00000011)

    unpacked = np.empty((b.shape[0] * 4,), dtype=np.uint16)
    unpacked[0::4] = p0
    unpacked[1::4] = p1
    unpacked[2::4] = p2
    unpacked[3::4] = p3

    return unpacked.reshape((h, w))

def raw10_to_video(
    raw_path: str,
    width: int,
    height: int,
    bayer: str,
    fps: int,
    out_path: str,
):
    frame_bytes = int(width * height * 1.25)
    file_size = os.path.getsize(raw_path)
    n_frames = file_size // frame_bytes

    if file_size % frame_bytes:
        raise ValueError(
            f"File size {file_size} is not an exact multiple of one RAW10 frame"
            f"({frame_bytes}). Check width/height."
        )

    print(f"{raw_path}: {n_frames} frames detected ({width}×{height} RAW10)")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

    with open(raw_path, "rb") as f:
        for idx in range(n_frames):
            chunk = f.read(frame_bytes)
            raw10 = unpack_raw10(chunk, height, width)

            # shift left to 16 bit so OpenCV sees correct bit-depth
            raw16 = (raw10.astype(np.uint16) << 6)

            rgb16 = cv2.cvtColor(raw16, BAYER_MAP[bayer])

            # compress to 8 bit for video
            rgb8 = (rgb16 >> 8).astype(np.uint8)  

            writer.write(rgb8)
            print(f"  frame {idx+1}/{n_frames}")

    writer.release()
    print(f"Saved {out_path}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Convert multi-frame RAW10 dump to an MP4 video"
    )
    ap.add_argument("raw", help="input .raw file that holds N RAW10 frames")
    ap.add_argument("--width", type=int, required=True)
    ap.add_argument("--height", type=int, required=True)
    ap.add_argument(
        "--bayer",
        choices=BAYER_MAP.keys(),
        default="BGGR",
        help="Bayer mosaic order (default BGGR)",
    )
    ap.add_argument("--fps", type=int, default=30, help="output frame-rate")
    ap.add_argument(
        "--out", default="output.mp4", help="output video path"
    )
    args = ap.parse_args()

    raw10_to_video(
        args.raw, args.width, args.height, args.bayer, args.fps, args.out
    )