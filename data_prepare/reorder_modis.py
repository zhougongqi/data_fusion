"""
read MODIS MOD09GA data and write them into tif file with landsat band order
"""
import os
import pprint
from osgeo import gdal
from os.path import join
import numpy as np
from datetime import datetime
import gc
import time


def create_tar_hdf(data_path, tile_key, start_time, end_time):
    """
       function to get a list of data file given time period and tileid
       """
    start_time = datetime.strptime(start_time, "%Y%m%d")
    end_time = datetime.strptime(end_time, "%Y%m%d")

    hdf_list = []
    for MOD11Folder in os.listdir(data_path):
        MOD11Date = datetime.strptime(MOD11Folder, "%Y.%m.%d")
        if start_time <= MOD11Date <= end_time:
            for MOD11_file in os.listdir(join(data_path, MOD11Folder)):
                if (MOD11_file.split(".")[-1] == "hdf") and (
                    MOD11_file.split(".")[2] in [tile_key]
                ):
                    hdf_list.append(join(data_path, MOD11Folder, MOD11_file))
        else:
            continue
    return hdf_list


def date2DOY(file_date):
    """
    function to convert date YYYYMMDD to day of year YYYYJJJ
    """
    file_date = datetime.strptime(file_date, "%Y%m%d")
    days = str(file_date.year).zfill(4) + str(file_date.timetuple().tm_yday).zfill(3)
    return days


def modis_2_tif(img_file_path: str, band_list: list, outdir: str):
    """
    get modis data , write them to tiff file

    img_file_path: input modis file path
    band_list:
    outdir:

    """
    MODIS_ds = gdal.Open(img_file_path)
    # Loop subdatasets to find right subdataset
    sd = MODIS_ds.GetSubDatasets()
    nbands = len(band_list)
    basename = os.path.basename(img_file_path)
    outpath = outdir + basename.replace(".hdf", ".reordered.tif")

    # read one to get some infos
    for subdataset in MODIS_ds.GetSubDatasets():
        band_name_check = [
            band_name
            for band_name in ["sur_refl_b04_1"]
            if (band_name in subdataset[1])
        ]
        if band_name_check == []:
            continue

        Band_ds = gdal.Open(subdataset[0])
        XSize = Band_ds.RasterXSize
        YSize = Band_ds.RasterYSize
        ds_proj = Band_ds.GetProjection()
        ds_geotrans = Band_ds.GetGeoTransform()
        Band_ds = None
        break

    # build a new tiff with 6 bands
    Image_ds = gdal.GetDriverByName("GTiff").Create(
        outpath, XSize, YSize, nbands, gdal.GDT_Int16
    )

    # read all bands and write them
    bn = 0
    for band in band_list:
        # loop band first to keep band order same with band_list
        for subdataset in MODIS_ds.GetSubDatasets():
            band_name_check = [
                band_name for band_name in [band] if (band_name in subdataset[1])
            ]
            if band_name_check == []:
                continue

            # if band name is valid, save subdataset to a tif image
            band_name = band_name_check[0]
            try:
                Band_ds = gdal.Open(subdataset[0])
            except Exception as e:
                print("open MODIS subdataset falied! ", subdataset[0])
                return False
            Band_array = Band_ds.GetRasterBand(1).ReadAsArray()
            bn += 1
            print(bn)
            Image_ds.GetRasterBand(bn).WriteArray(Band_array)
    Image_ds.SetProjection(ds_proj)
    Image_ds.SetGeoTransform(ds_geotrans)
    Image_ds.FlushCache()
    Image_ds = None

    return True


if __name__ == "__main__":

    modpath = "/home/tq/data_pool/zgq/estarfm/modis/MOD09GA.A2018257.h26v04.006.2018259031729.hdf"
    bandlist = [
        "sur_refl_b03_1",
        "sur_refl_b04_1",
        "sur_refl_b01_1",
        "sur_refl_b02_1",
        "sur_refl_b06_1",
        "sur_refl_b07_1",
    ]
    outdir = "/home/tq/data_pool/zgq/estarfm/modis_reorder/"
    stat = modis_2_tif(modpath, bandlist, outdir)
