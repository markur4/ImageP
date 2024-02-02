""" Utility functions to import images from various formats. """
# %%
import numpy as np

import matplotlib.pyplot as plt

import skimage as ski


# > Local
import imagep._utils.utils as ut
import imagep._rc as rc

# %%
# == Import from txt ===================================================


def from_txt(
    path: str, skiprows: int = None, dtype=rc.DTYPE_DEFAULT
) -> np.ndarray:
    """Import from a txt file."""

    if not skiprows is None:
        return np.loadtxt(path, skiprows=skiprows).astype(dtype)

    ### Skip rows until image is succesfully imported
    else:
        for i in range(3):  # > maximum 3 rows to skip
            try:
                return np.loadtxt(path, skiprows=i).astype(dtype)
            except:
                continue

    return np.loadtxt(path, skiprows=skiprows).astype(dtype)


if __name__ == "__main__":
    t = np.float32
    # path = "/Users/martinkuric/_REPOS/ImageP/ANALYSES/data/231215_adipose_tissue/1 healthy z-stack rough/Image3_6.txt"
    # img = from_txt(path, type=t)
    # print(img.min(), img.max())
    # plt.imshow(img)
    # plt.show()

    path = "/Users/martinkuric/_REPOS/ImageP/ANALYSES/data/231215_adipose_tissue/1 healthy z-stack rough/Image3_7.txt"
    img = from_txt(path, dtype=t)
    print(img.min(), img.max())
    plt.imshow(img)

    # %%
    ### Find smallest difference
    img_diff = ski.filters.sobel(img)
    print(img_diff.min(), img_diff.max())
    plt.imshow(img_diff)

# %%
# == Import from Image formats =========================================