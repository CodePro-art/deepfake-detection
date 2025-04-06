import torch
from torch.utils.data import Dataset
from torchvision.io import read_video
from torch import nn
import json
from os import path
from typing import TypedDict, Union, Optional, Literal, List, Tuple, Callable
from typing_extensions import Self
import glob

# Define type aliases for better readability
Split = Union[Literal['train'], Literal['validation']]
Label = Union[Literal[0], Literal[1]]

# Define a TypedDict for file metadata
class FileMetadata(TypedDict):
    path: str
    label: Label
    original: Optional[str]

class VideoDataset(Dataset):
    def __init__(self: Self, root_path: str, split: Split, transform: Optional[Callable] = None, target_transform: Optional[Callable] = None):
        self.root_path = root_path
        self.transform = transform
        self.target_transform = target_transform

        # Initialize metadata list
        self.metadata: List[FileMetadata] = []

        # Collect metadata file paths using glob
        metadata_paths = glob.glob(path.join(root_path, '**/metadata.json'), recursive=True)
        
        # Load and parse metadata files
        for metadata_path in metadata_paths:
            with open(metadata_path) as file:
                metadata = json.load(file)
            
            for k, data in metadata.items():
                if data['split'] != split:
                    continue

                video_path = path.join(path.dirname(metadata_path), k)
                data['path'] = video_path
                data['label'] = 1 if data['label'] == 'FAKE' else 0
                del data['split']  # Remove 'split' key as it is no longer needed

                self.metadata.append(data)

    def __getitem__(self: Self, index: int) -> Tuple[torch.Tensor, Label]:
        metadata = self.metadata[index]
        video_path = metadata['path']

        # Read video and discard audio and info (underscore variables)
        video, _, _ = read_video(video_path, pts_unit='sec', end_pts=9)
        
        if self.transform:
            video = self.transform(video)
        
        label = metadata['label']
        
        if self.target_transform:
            label = self.target_transform(label)

        return video, label

    def __len__(self: Self) -> int:
        return len(self.metadata)

# Example usage:
# dataset = VideoDataset(root_path='path/to/data', split='train', transform=some_transform, target_transform=some_target_transform)
