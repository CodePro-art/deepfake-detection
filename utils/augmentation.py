import random
import cv2
import numpy as np
from albumentations import DualTransform, ImageOnlyTransform
from albumentations import Crop


def isotropically_resize_image(img, size, interpolation_down=cv2.INTER_AREA, interpolation_up=cv2.INTER_CUBIC):
    """
    Resize an image maintaining its aspect ratio.

    Args:
    - img (numpy.ndarray): The input image.
    - size (int): The maximum side length after resizing.
    - interpolation_down (int): Interpolation method for scaling down.
    - interpolation_up (int): Interpolation method for scaling up.

    Returns:
    - numpy.ndarray: Resized image.
    """
    h, w = img.shape[:2]
    if max(w, h) == size:
        return img
    if w > h:
        scale = size / w
        h = h * scale
        w = size
    else:
        scale = size / h
        w = w * scale
        h = size
    interpolation = interpolation_up if scale > 1 else interpolation_down
    return cv2.resize(img, (int(w), int(h)), interpolation=interpolation)


class IsotropicResize(DualTransform):
    """
    Augmentation to isotropically resize an image.
    """

    def __init__(self, max_side, interpolation_down=cv2.INTER_AREA, interpolation_up=cv2.INTER_CUBIC,
                 always_apply=False, p=1):
        super(IsotropicResize, self).__init__(always_apply=always_apply, p=p)
        self.max_side = max_side
        self.interpolation_down = interpolation_down
        self.interpolation_up = interpolation_up

    def apply(self, img, **params):
        """
        Apply isotropic resize transformation to an image.

        Args:
        - img (numpy.ndarray): The input image.
        - **params: Additional parameters.

        Returns:
        - numpy.ndarray: Resized image.
        """
        return isotropically_resize_image(img, size=self.max_side,
                                          interpolation_down=self.interpolation_down,
                                          interpolation_up=self.interpolation_up)

    def apply_to_mask(self, img, **params):
        """
        Apply transformation to masks.

        Args:
        - img (numpy.ndarray): The input mask image.
        - **params: Additional parameters.

        Returns:
        - numpy.ndarray: Transformed mask image.
        """
        return self.apply(img, interpolation_down=cv2.INTER_NEAREST, interpolation_up=cv2.INTER_NEAREST, **params)

    def get_transform_init_args_names(self):
        return ("max_side", "interpolation_down", "interpolation_up")


class Resize4xAndBack(ImageOnlyTransform):
    """
    Augmentation to resize an image 4 times down and back to original size.
    """

    def __init__(self, always_apply=False, p=0.5):
        super(Resize4xAndBack, self).__init__(always_apply=always_apply, p=p)

    def apply(self, img, **params):
        """
        Apply resize 4x and back transformation to an image.

        Args:
        - img (numpy.ndarray): The input image.
        - **params: Additional parameters.

        Returns:
        - numpy.ndarray: Transformed image.
        """
        h, w = img.shape[:2]
        scale = random.choice([2, 4])
        img = cv2.resize(img, (w // scale, h // scale), interpolation=cv2.INTER_AREA)
        img = cv2.resize(img, (w, h),
                         interpolation=random.choice([cv2.INTER_CUBIC, cv2.INTER_LINEAR, cv2.INTER_NEAREST]))
        return img


class RandomSizedCropNonEmptyMaskIfExists(DualTransform):
    """
    Augmentation to perform random sized crop based on non-empty mask.
    """

    def __init__(self, min_max_height, w2h_ratio=None, always_apply=False, p=0.5):
        super(RandomSizedCropNonEmptyMaskIfExists, self).__init__(always_apply=always_apply, p=p)
        self.min_max_height = min_max_height
        self.w2h_ratio = w2h_ratio if w2h_ratio is not None else [0.7, 1.3]


    def apply(self, img, x_min=0, x_max=0, y_min=0, y_max=0, **params):
        """
        Apply random sized crop transformation to an image.

        Args:
        - img (numpy.ndarray): The input image.
        - x_min (int): Minimum x-coordinate for cropping.
        - x_max (int): Maximum x-coordinate for cropping.
        - y_min (int): Minimum y-coordinate for cropping.
        - y_max (int): Maximum y-coordinate for cropping.
        - **params: Additional parameters.

        Returns:
        - numpy.ndarray: Cropped image.
        """
        return Crop(img, x_min, y_min, x_max, y_max)

    @property
    def targets_as_params(self):
        return ["mask"]

    def get_params_dependent_on_targets(self, params):
        """
        Generate parameters dependent on target (mask).

        Args:
        - params (dict): Dictionary containing parameters.

        Returns:
        - dict: Generated parameters.
        """
        mask = params["mask"]
        mask_height, mask_width = mask.shape[:2]
        crop_height = int(mask_height * random.uniform(self.min_max_height[0], self.min_max_height[1]))
        w2h_ratio = random.uniform(*self.w2h_ratio)
        crop_width = min(int(crop_height * w2h_ratio), mask_width - 1)
        if mask.sum() == 0:
            x_min = random.randint(0, mask_width - crop_width + 1)
            y_min = random.randint(0, mask_height - crop_height + 1)
        else:
            mask = mask.sum(axis=-1) if mask.ndim == 3 else mask
            non_zero_yx = np.argwhere(mask)
            y, x = random.choice(non_zero_yx)
            x_min = x - random.randint(0, crop_width - 1)
            y_min = y - random.randint(0, crop_height - 1)
            x_min = np.clip(x_min, 0, mask_width - crop_width)
            y_min = np.clip(y_min, 0, mask_height - crop_height)

        x_max = x_min + crop_height
        y_max = y_min + crop_width
        y_max = min(mask_height, y_max)
        x_max = min(mask_width, x_max)
        return {"x_min": x_min, "x_max": x_max, "y_min": y_min, "y_max": y_max}

    def get_transform_init_args_names(self):
        return "min_max_height", "w2h_ratio"
