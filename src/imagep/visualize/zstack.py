#
# %%

import numpy as np

import matplotlib.pyplot as plt

plt.rcParams["figure.dpi"] = 250

import vtk
from vtk.util import numpy_support
import pyvista as pv

# > Local
from imagep.processing.preprocess import PreProcess
import imagep._plots.imageplots as ut

# %%


class ZStack(PreProcess):
    def __init__(
        self,
        # imgs,
        *imgs_args,
        z_dist,
        pixel_length: float = None,
        scalebar: bool = True,
        # remove_empty_slices: bool = True,
        **preprocess_kws,
    ):
        """Visualize Z-stacks.
        :param z_dist: Distance between two images in µm
        :type z_dist: float
        :param scalebar: Switches on scalebar, defaults
            to True
        :type scalebar: bool, optional
        :param imgs_args: positional arguments passed to Imgs class
        :type imgs_args: tuple
        :param preprocess_kws: Keyword arguments passed to
        PreProcess class
        """
        super().__init__(*imgs_args, **preprocess_kws)

        # self.imgs = imgs

        print(f"{type(self.imgs)=}")
        print(f"{self.imgs[0].pixel_length=}")

        ### Burn Scalebar into the first image:
        # > This is very awesome for volume rendering!
        self.scalebar = scalebar
        if scalebar:
            self.imgs[0] = self.burn_scalebars()[0]

        ### Z-distance
        self.z_dist = z_dist

        ### Retrieve pixel_length, since it's useful
        if pixel_length is not None:
            self.pixel_length = pixel_length
        elif hasattr(self.imgs[0], "pixel_length"):
            self.pixel_length = self.imgs[0].pixel_length
        else:
            raise ValueError(
                "pixel_length not provided and not found in the images"
            )

        ### Fill z
        self.imgs_zfilled = self.fill_z()

        ### Remove empty slices
        # if remove_empty_slices:
        #     self.imgs_zfilled = self.remove_empty_slices(self.imgs_zfilled)

    # ==================================================================
    # == Utils =========================================================

    def fill_z(self) -> np.ndarray:
        """Each pixel has a length in µm. Consider each image as a pixel
        in z-direction. This function duplicates images so that each
        image has a thickness of z_dist in µm"""

        ### Calculate number how often each image has to be repeated
        thickness_pixel = self.z_dist / self.pixel_length
        thickness_pixel = int(round(thickness_pixel))

        ### Duplicate images n times so that each layer has thickness
        # ' of µm
        stack = []
        for img in self.imgs:
            for _ in range(thickness_pixel):
                stack.append(img)

        ### Convert to numpy array
        stack = np.array(stack)
        return stack

    # == __str__ ======================================================

    @property
    def _info_ZStack(self):
        adj = self._adj
        ID = self._info

        ### Append Z Information to "Distance"
        ID["Distance"] = ID["Distance"] + [
            adj("pixel size z") + f"{self.z_dist}",
            adj("z") + f"{self.z_dist * self.imgs.shape[0]}",
        ]

        return ID

    def __str__(self) -> str:
        return self._info_to_str(self._info_ZStack)

    # ==================================================================
    # == Plotting ======================================================

    def mip(self, **mip_kws) -> np.ndarray | None:
        """Maximum intensity projection across certain axis"""
        #!! Overrides PreProcess.mip(), so that correct z-axis dimension
        #!! is used

        return ut.plot_mip(imgs=self.imgs_zfilled, **mip_kws)

    @property
    def stack_vtk(self):
        stack = self.imgs_zfilled

        ### Transpose the numpy array to match PyVista's x, y, z convention
        stack = np.transpose(stack, axes=[2, 1, 0])

        ### Convert numpy array to VTK array
        vtk_data_array = numpy_support.numpy_to_vtk(
            num_array=stack.ravel(order="F"),
            deep=True,
            array_type=vtk.VTK_FLOAT,
        )

        ### Create vtkImageData object
        vtk_image_data = vtk.vtkImageData()
        vtk_image_data.SetDimensions(stack.shape)
        vtk_image_data.GetPointData().SetScalars(vtk_data_array)

        return vtk_image_data

    @property
    def stack_pyvista(self):
        return pv.ImageData(self.stack_vtk)

    def plot_volume(
        self,
        cmap="viridis",
        show=True,
        ret=False,
        **plot_kws,
    ) -> pv.Plotter:
        """Makes a Plotter object with the volume added"""
        ### Plot
        volplot = pv.Plotter()

        ### Add volume
        volplot.add_volume(
            self.stack_pyvista,
            cmap=cmap,
            # opacity="sigmoid",
            **plot_kws,
        )

        ### Edits
        # > Bounding Box
        volplot.add_bounding_box(color="#00000050")  # > transparent black
        # > Camera Position
        volplot.camera.roll = 180

        ### Return
        if show:
            volplot.show()
        if ret:
            return volplot

    def makegif_rotate(
        self,
        fname: str = "rotate.gif",
        angle_per_frame=1,
    ):
        ### Initialize plotter
        if self.verbose:
            print("=> Initializing plotter ...")
        volplot = self.plot_volume(show=False, ret=True)

        # > Set initial camera position
        volplot.camera_position = "xy"
        volplot.camera.roll = 180
        # pl.camera.roll = 45

        # > Adjust clipping range
        # pl.camera.clipping_range = self.stack.shape[1:2]
        volplot.camera.clipping_range = (1000, 5000)

        ### Write Animation
        if self.verbose:
            print(f"=> Writing {self.imgs_zfilled.shape}, '{fname}' ...")

        # > Open GIF
        if not fname.endswith(".gif"):
            fname += ".gif"
        volplot.open_gif(fname)

        self.rotate_and_write(
            volplot,
            start=0,
            stop=360,
            angle_per_frame=angle_per_frame,
            # parallel=True,
        )

        volplot.close()

    @staticmethod
    def rotate_and_write(
        volplot: pv.Plotter,
        start: int = 0,
        stop: int = 360,
        angle_per_frame: int = 3,
    ):
        # > Rotate & Write
        for angle in range(start, stop, angle_per_frame):
            ### adjust zoom to keep object in frame

            volplot.camera.azimuth = angle
            volplot.render()
            volplot.write_frame()

    # !! == End Class ==================================================


if __name__ == "__main__":
    pass
    # %%
    ### Import from a txt file.
    # > Rough
    path_rough = "/Users/martinkuric/_REPOS/ImageP/ANALYSES/data/231215_adipose_tissue/1 healthy z-stack rough/"
    kws = dict()
    # %%
    I = 8
    Z = PreProcess(
        data=path_rough,
        fname_extension=".txt",
        imgname_position=1,
        denoise=True,
        normalize="stack",
        subtract_bg=True,
        subtract_bg_kws=dict(
            method="otsu",
            sigma=3,
            per_img=False,
        ),
        scalebar_length=10,
        snapshot_index=I,
        remove_empty_slices=True,
        pixel_length=(1.5 * 115.4)
        / 1024,  # fast axis amplitude 1.5 V * calibration 115.4 µm/V
        **kws,
    )
    #%%
    Z.imgs[0].pixel_length

    # %%
    ZS = ZStack(
        data=Z,
        pixel_length=(1.5 * 115.4)/1024,
        z_dist=10 * 0.250,  # stepsize * 0.250 µm
    )
    # %%
    ZS.mip(axis=0)
    ZS.mip(axis=1)
    ZS.mip(axis=2)
    # %%
    ### make gif of rough
    ZS.info
    # %%
    ZS.mip()
    # %%
    # Z2.plot_volume()
    # %%
    ZS.makegif_rotate(fname="rotate_rough_scalebar=10", angle_per_frame=3)

    # %%
    ### make gif for detailed!
    # > Detailed
    path_detailed = "/Users/martinkuric/_REPOS/ImageP/ANALYSES/data/231215_adipose_tissue/2 healthy z-stack detailed/"
    kws_detailed = dict(
        z_dist=2 * 0.250,  # stepsize * 0.250 µm
        x_µm=1.5 * 115.4,  # fast axis amplitude 1.5 V * calibration 115.4 µm/V
    )

    Z_d = ZStack(
        path=path_detailed,
        denoise=True,
        subtract_bg=True,
        remove_empty_slices=True,
        **kws_detailed,
    )
    Z_d
    # %%
    Z_d.makegif_rotate(fname="rotate_detailed_scalebar=10", angle_per_frame=3)
