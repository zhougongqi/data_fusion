import os
import pprint
from osgeo import gdal
from os.path import join
import numpy as np
from datetime import datetime
import gc
import time

import matplotlib.pyplot as pyplot


def hist_match(source, template):
    """
    Adjust the pixel values of a grayscale image such that its histogram
    matches that of a target image

    Arguments:
    -----------
        source: flattened np.ndarray
            Image to transform; the histogram is computed over the flattened
            array
        template: np.ndarray
            Template image; can have different dimensions to source
    Returns:
    -----------
        matched: flattened np.ndarray
            The transformed output image
    """
    # oldshape = source.shape
    # source = source.ravel()
    # template = template.ravel()

    # get the set of unique pixel values and their corresponding indices and
    # counts
    s_values, bin_idx, s_counts = np.unique(
        source, return_inverse=True, return_counts=True
    )
    t_values, t_counts = np.unique(template, return_counts=True)

    # take the cumsum of the counts and normalize by the number of pixels to
    # get the empirical cumulative distribution functions for the source and
    # template images (maps pixel value --> quantile)
    s_quantiles = np.cumsum(s_counts).astype(np.float64)
    s_quantiles /= s_quantiles[-1]
    t_quantiles = np.cumsum(t_counts).astype(np.float64)
    t_quantiles /= t_quantiles[-1]

    # interpolate linearly to find the pixel values in the template image
    # that correspond most closely to the quantiles in the source image
    interp_t_values = np.interp(s_quantiles, t_quantiles, t_values)

    return interp_t_values[bin_idx]


if __name__ == "__main__":

    fullimg = "/home/tq/data_pool/zgq/estarfm/test/sub-0802.tif"  # full img
    gapimg = "/home/tq/data_pool/zgq/estarfm/test/sub-0818.tif"  # img with gap

    # read img
    ds = gdal.Open(fullimg)
    geo_trans = ds.GetGeoTransform()
    w = ds.RasterXSize
    h = ds.RasterYSize
    img_shape = [h, w]
    proj = ds.GetProjection()
    arrfull = ds.GetRasterBand(4).ReadAsArray()
    ds = None

    ds = gdal.Open(gapimg)
    geo_trans = ds.GetGeoTransform()
    w = ds.RasterXSize
    h = ds.RasterYSize
    img_shape = [h, w]
    proj = ds.GetProjection()
    arrgap = ds.GetRasterBand(4).ReadAsArray()
    ds = None

    # get mask of gap
    mask = arrgap.copy()
    mask[mask > 0] = 1
    mask[mask <= 0] = 0  # zero is cloud
    maxv = np.max(arrfull) / 5  # np.percentile(arrfull, 0.7) / 5  #

    fill = arrfull.copy()
    idx0 = np.where(mask == 0)
    idx1 = np.where(mask == 1)
    fill[idx1] = 0

    # valid pixels = vp
    vp_fill = fill[idx0]
    vp_gap = arrgap[idx1]

    vp_fill = hist_match(vp_fill, vp_gap)
    fill[idx0] = vp_fill

    arrgapnew = arrgap + fill

    pyplot.figure(num="test", figsize=(8, 8))  # image show part
    p1 = pyplot.subplot(131)
    p2 = pyplot.subplot(132)
    p3 = pyplot.subplot(133)
    p1.imshow(arrfull, cmap=pyplot.cm.rainbow, vmin=0., vmax=maxv)
    p2.imshow(arrgap, cmap=pyplot.cm.rainbow, vmin=0., vmax=maxv)
    p3.imshow(arrgapnew, cmap=pyplot.cm.rainbow, vmin=0., vmax=maxv)
    pyplot.show()  # image show part end

    print("fin")
