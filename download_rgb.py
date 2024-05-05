# loading Libaries
import openeo
import os
from time import sleep

# defining the function to download the RGB data
def download_rgb(extent):

    beginning = extent["beginning"]
    ending = extent["ending"]
    west = extent["west"]
    south = extent["south"]
    east = extent["east"]
    north = extent["north"]
    path = extent["path"]
    name = extent["name"]

    suggsess = False
    while suggsess is not True:
        try:
            os.makedirs(path)
            suggsess = True
        except FileExistsError:
            path = path + '_new'

    datacube = connection.load_collection(
        'SENTINEL2_L2A',
        spatial_extent={
            'west': west, 
            'south': south, 
            'east': east, 
            'north': north,
            'crs': 'EPSG:4326'},
        temporal_extent=[f'{beginning}', f'{ending}'],
        bands=['B02', 'B03', 'B04'],
        max_cloud_cover=85,
    )

    datacube.download(f'{path}/{name}.nc')

# running the script
if __name__ == '__main__':

    # defining the extents
    extent1 = {
        "beginning": "2022-01-01",
        "ending": "2022-04-30",
        "west": 22.45,
        "south": 2.4,
        "east": 22.65,
        "north": 2.6,
        "path": 'data/extent01',
        "name": 'bumba_RGB_ex1'
    }

    extent2 = {
        "beginning": "2020-05-01",
        "ending": "2020-08-31",
        "west": 22.6,
        "south": 2.4,
        "east": 22.8,
        "north": 2.6,
        "path": 'data/extent02',
        "name": 'bumba_RGB_ex2'
    }

    extents = [extent1, extent2]

    # connecting to the openEO backend
    connection = openeo.connect('openeo.dataspace.copernicus.eu')
    connection.describe_collection('SENTINEL2_L2A')
    connection.authenticate_oidc()

    # downloading the data
    for extent in extents:
        download_rgb(extent)
        sleep(5)