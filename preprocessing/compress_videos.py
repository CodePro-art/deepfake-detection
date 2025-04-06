import argparse
import os
import random
import subprocess
import numpy as np
import torch
from functools import partial
from glob import glob
from multiprocessing.pool import Pool
from os import cpu_count
import cv2 as cv
from tqdm import tqdm

def compress_video(filepath, down_fps, scale_fact, isGray):
    
    print(f"Compressing video: {filepath} with down_fps: {down_fps}, scale_fact: {scale_fact}, isGray: {isGray}", flush=True)
    REF_HEIGHT, REF_WIDTH = 1080, 1920
    down_height, down_width = round(REF_HEIGHT / scale_fact), round(REF_WIDTH / scale_fact)
    down_points = (down_width, down_height)

    cap = cv.VideoCapture(filepath)
    fps = cap.get(cv.CAP_PROP_FPS)
    if fps == 0:
        # raise ValueError(f"Could not read FPS from {filepath}")
        return None
    fcnt = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
    fps_factor = round(fps / down_fps)
    num_frames = round(fcnt / fps_factor)

    # Define color conversion function based on isGray
    color_conversion = lambda x: cv.cvtColor(x, cv.COLOR_BGR2GRAY) if isGray else cv.cvtColor(x, cv.COLOR_BGR2RGB)

    # Preallocate video tensor
    video_shape = (num_frames, down_height, down_width) if isGray else (num_frames, down_height, down_width, 3)
    video = np.empty(video_shape, dtype=np.uint8)

    # Read video frames and store them in the tensor
    for frame_idx in range(fcnt):
        if not cap.isOpened():
            break
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % fps_factor != 0:
            continue

        height, width, _ = frame.shape
        if height > width:
            frame = cv.rotate(frame, cv.ROTATE_90_CLOCKWISE)

        frame_sample = cv.resize(color_conversion(frame), down_points, interpolation=cv.INTER_LINEAR)
        new_index = round(frame_idx / fps_factor)
        try:
            if new_index < num_frames:
                video[new_index,:,:,:] = frame_sample
        except IndexError:
            print(f"IndexError: Attempted to access index {frame_idx // fps_factor} in video_shape {video_shape}")
            raise 

        frame_idx += 1

    cap.release()
    cv.destroyAllWindows()

    return torch.tensor(video)

def process_chunk(chunk_id, chunk_indices, meta_df, progress_dict=None):
    grayscale = False
    new_fps = 10
    scale_factor = 20
    
    if progress_dict is None:
        return None
    
    chunk_df = meta_df.iloc[chunk_indices]
    chunk_df = chunk_df.reset_index()
    tensors = []
    for index, row in chunk_df.iterrows():
        source_path = os.path.join(row['path'], row['filename'])
        tensor_dir = row['path-compressed']
        tensor_name = f"{row['filename'][:-4]}.tns"
        tensor_path = os.path.join(tensor_dir, tensor_name)
                
        # Ensure directory exists
        if not os.path.exists(tensor_dir):
            os.makedirs(tensor_dir)
        if not os.path.exists(tensor_path):
            tensor = compress_video(source_path, new_fps, scale_factor, grayscale)
            if tensor is None:
                print(f"Failed to compress {source_path}")
                continue
            os.makedirs(os.path.dirname(tensor_path), exist_ok=True)
            # Update the progress
            progress_dict[chunk_id] += 1
            torch.save(tensor, tensor_path)
            tensors.append((tensor, tensor_path))
        
    return tensors
