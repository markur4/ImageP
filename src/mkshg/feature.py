"""Module to extract features from SHG images"""

# %%
import os

import numpy as np
import matplotlib.pyplot as plt

### Increase display dpi of matplotlib
plt.rcParams["figure.dpi"] = 200
import seaborn as sns

from skimage import filters
from sklearn.ensemble import RandomForestClassifier

from import_and_preprocess import PreProcess
from zstack import ZStack

# %%

# ==================================================================


class Segmentation(PreProcess):
    def __init__(self, **preprocess_kwargs):
        super().__init__(**preprocess_kwargs)

        ### Calculate fiber width
        # self.fiber_width = self.measure_fiber_width()

    # ==================================================================

    # def threshold(self, img: np.ndarray, threshold: float = 0.06) -> np.ndarray:

    # def measure_fiber_width(self) -> np.ndarray:
    #     """Measure fiber width for each pixel in each image"""

    #     ### Calculate fiber width
    #     fiber_width = np.zeros(self.stack_zfilled.shape)
    #     for i, img in enumerate(self.stack_zfilled):
    #         fiber_width[i] = self._measure_fiber_width(img)

    #     return fiber_width

    # def measure_fiber_width(self, img: np.ndarray) -> np.ndarray:
    #     """Measure fiber width for each pixel in an image"""

    #     ### Calculate fiber width
    #     fiber_width = 0

    #     return fiber_width


if __name__ == "__main__":
    path = "/Users/martinkuric/_REPOS/a_shg_collagen/ANALYSES/data/231215_adipose_tissue/1 healthy z-stack rough/"

    # %%
    Z = ZStack(
        path=path,
        denoise=True,
        subtract_bg=True,
        scalebar_μm=False,
        z_dist=10 * 0.250,  # stepsize * 0.250 µm
    )
    Z.mip()

    # %%
    F = Z.stack[9]
    print(F.shape)
    plt.imshow(F)

    # %%
    ### test different thresholding methods
    from skimage import feature

    # %%
    print("sigma=1.0")
    F_canny_1 = feature.canny(F, sigma=1.0)
    plt.imshow(F_canny_1)

    # %%
    print("sigma=1.5")
    F_canny_1 = feature.canny(F, sigma=1.5)
    plt.imshow(F_canny_1)

    # %%
    print("sigma=2")
    F_canny_1 = feature.canny(F, sigma=2)
    plt.imshow(F_canny_1)

    # %% ===============================================================
    # == Threshold with Machine Learning ===============================

    # %%
    ### Extract Features

    from skimage import filters

    def make_feature_stack(image, sigma=1):
        ### Define features
        blurred = filters.gaussian(image, sigma=sigma)
        # > Edge Detection
        prewitt = filters.prewitt(blurred)
        sobel = filters.sobel(blurred)
        canny1 = feature.canny(blurred, sigma=1)  # > Detailed edges
        canny2 = feature.canny(blurred, sigma=2)  # > Rough edges

        ### Collect features in a stack
        # > The ravel() function turns a nD image into a 1-D image.
        #  > We need to use it because scikit-learn expects values in a 1-D format here.
        feature_stack: list[np.ndarray] = [
            image.ravel(),
            blurred.ravel(),
            prewitt.ravel(),
            sobel.ravel(),
            canny1.ravel(),
            canny2.ravel(),
        ]

        return np.asarray(feature_stack)

    feature_stack = make_feature_stack(F)

    # %%

    ### show feature images
    import matplotlib.pyplot as plt

    names = [
        "Image",
        "blurred",
        "prewitt",
        "sobel",
        "canny\nsigma=1",
        "canny\nsigma=2",
    ]

    h = 2
    w = int(feature_stack.shape[0] / h)
    fig, axes = plt.subplots(h, w, figsize=(w * 5, h * 5))
    plt.subplots_adjust(wspace=0.03, hspace=0.2)

    for ax, img, name in zip(axes.flatten(), feature_stack, names):
        ax.imshow(img.reshape(F.shape), cmap=plt.cm.gray)
        ax.axis("off")
        ax.set_title(name)

    # %%
    def mask_by_annotation(feature_stack: np.ndarray, annotation: np.ndarray):
        """Reformat the data to match what scikit-learn expects"""
        ### Transpose the feature stack
        X = feature_stack.T
        ### Make the annotation 1-dimensional
        y = annotation.ravel()

        ### Remove all pixels from the feature and annotations which have not been annotated
        mask = y > 0
        X = X[mask]
        y = y[mask]

        return X, y

    # # %%
    # ### Pseudo-annotation
    # annotation = np.zeros(F.shape)
    # annotation[0:10, 0:10] = 1
    # annotation[45:55, 10:20] = 2

    # plt.imshow(annotation)

    # X, y = apply_annotation(feature_stack, annotation)

    # print("input shape", X.shape)
    # print("annotation shape", y.shape)

    # %%
    ### TRAIN
    # _classifier = RandomForestClassifier(max_depth=2, random_state=0)
    # _classifier.fit(X, y)

    # %%
    # ### PREDICT
    # # > we subtract 1 to make background = 0
    # res = _classifier.predict(feature_stack.T) - 1

    # plt.imshow(F)
    # plt.show()
    # plt.imshow(res.reshape(F.shape))
    # plt.show()

# %%
### == MANUAL ANNOTATION ===============================================
import napari

### Open Viewer and ADd raw image
viewer = napari.Viewer()

#%%
viewer.add_image(F, name="raw")

# %%
### Add an empty labels layer and keet it in a variable
labels = viewer.add_labels(np.zeros(F.shape).astype(int), name="labels")

# %%
### Show annotations
manual_annotations = labels.data
plt.imshow(manual_annotations, vmin=0, vmax=2)


# %%
def open_annotations(
    fname="_annot_cache.npy",
) -> None | np.ndarray:
    """Load the annotations from the hard drive and display them in the viewer"""
    if not os.path.exists(fname):
        print("No annotations found")
        return
    with open(fname, "rb") as f:
        A = np.load(f)

    return A


plt.imshow(open_annotations())

#%%
def update_annotations(viewer: napari.Viewer = None, fname="_annot_cache.npy",):
    """Cache the current annotations in the viewer onto the hard
    drive and load them again when the viewer is opened again"""

    ### no viewer
    if viewer is None:
        print(f"No viewer, opening {fname}")
        return open_annotations(fname)

    ### File not existing
    if not os.path.exists(fname):
        print(f"Saving annotations to {fname}")
        np.save(fname, viewer.layers["labels"].data)
        A_viewer = viewer.layers["labels"].data

    ### File exists
    else:
        A_hd: np.ndarray = open_annotations(fname)
        A_viewer: np.ndarray = viewer.layers["labels"].data

        ### Viewer empty
        if A_viewer is None:
            print("Adding saved annotations to viewer")
            # > Display the annotations in the current viewer
            viewer.layers["labels"].data = A_hd
            A_viewer = A_hd

        ### Viewer matches the cached annotations
        elif np.array_equal(A_hd, A_viewer):
            print("Nothing done: Saved annotations match those in viewer")

        ### Viewer not matching the saved annotations
        elif not np.array_equal(A_hd, A_viewer):
            print("Updating annotations from viewer to hard drive")
            ### hd to viewer
            A_viewer[A_hd > 0] = A_hd[A_hd > 0]

            ### viewer to hd
            # A_hd[A_viewer > 0] = A_viewer[A_viewer > 0]

            # > Display the annotations in the current viewer
            viewer.layers["labels"].data = A_viewer

            np.save(fname, A_viewer)
    return A_viewer


manual_annotations = update_annotations(
    viewer=viewer,
    fname="_annot_cache.npy",
)
plt.imshow(manual_annotations)


# %%
### Train and predict
# generate features (that's actually not necessary,
# as the variable is still there and the image is the same.
# but we do it for completeness)
feature_stack = make_feature_stack(F)
X, y = mask_by_annotation(feature_stack, manual_annotations)

# train classifier
classifier = RandomForestClassifier(max_depth=3, random_state=0)
classifier.fit(X, y)

# process the whole image and show result
result_1d = classifier.predict(feature_stack.T)
result_2d = result_1d.reshape(F.shape)
plt.imshow(
    result_2d,
    # cmap=("red", "blue", "purple"),
)

#%%
plt.imshow(F)

# %%
### compare with non AI segmentation filtering
# filter_image(F_blur, method="mean")
