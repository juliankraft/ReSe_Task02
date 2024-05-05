# loading Libaries
import openeo
from tqdm import tqdm
import os
from time import sleep

# defining functions to handle Months lengths considering leap years
def is_leap_year(year):
    """Returns True if the given year is a leap year, False otherwise."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

def get_month_lengths(year):
    """Returns a dictionary with the months as zero-padded strings and the number of days as values, adjusted for leap years."""
    return {
        "01": 31,
        "02": 29 if is_leap_year(year) else 28,
        "03": 31,
        "04": 30,
        "05": 31,
        "06": 30,
        "07": 31,
        "08": 31,
        "09": 30,
        "10": 31,
        "11": 30,
        "12": 31
    }

# handling output

output = False

# connecting to the openEO backend
connection = openeo.connect('openeo.dataspace.copernicus.eu')
connection.describe_collection('SENTINEL2_L2A')
connection.authenticate_oidc()

# defining the spatial and temporal extent
years = [str(y) for y in range(2022, 2024)] # end year not included
months = [str(y).zfill(2) for y in range(1, 13)] # end month not included

# bumba extent
west =22.2
south =2.1
east =22.8
north =2.6

# creating a directory to store the downloaded data
path = 'data/run02'
name = 'bumba_NDVI'

suggsess = False
while suggsess is not True:
    try:
        os.makedirs(path)
        suggsess = True
    except FileExistsError:
        path = path + '_new'

# starting Tasks year by year
for year in tqdm(years, desc='Downloading data'):
    month_lengths_list = get_month_lengths(int(year))
    for month in months:
        month_length = month_lengths_list[month]
            
        try:    
            datacube = connection.load_collection(
                'SENTINEL2_L2A',
                spatial_extent={
                    'west': west, 
                    'south': south, 
                    'east': east, 
                    'north': north,
                    'crs': 'EPSG:4326'},
                temporal_extent=[f'{year}-{month}-01', f'{year}-{month}-{month_length}'],
                bands=['B02', 'B03', 'B04', 'B08', 'SCL'],
                max_cloud_cover=85,
            )



            # selecting individual bands from the data cube and rescaling the digital number values to physical reflectances
            red = datacube.band('B04') * 0.0001
            nir = datacube.band('B08') * 0.0001

            scl_band = datacube.band('SCL')

            # computing NDVI
            ndvi = (nir - red) / (nir + red)

            # Resample the EVI cube to the spatial resolution of the mask (SCL band has a resolution of 20m, B04 and B08 have a resolution of 10m)
            ndvi_resampled = ndvi.resample_cube_spatial(scl_band)

            # Label NDVI and SCL bands
            ndvi_resampled = ndvi_resampled.add_dimension("bands", "NDVI", type="bands")
            scl_band = scl_band.add_dimension("bands", "SCL", type="bands")

            # Merge NDVI and SCL bands into a single cube
            output_cube = ndvi_resampled.merge_cubes(scl_band)


            # download the data

            output_cube.download(f'{path}/{name}_{year}{month}.nc')
        
        except openeo.rest.OpenEoApiError as e:
            with open(f'{path}/log.txt', 'a') as f:
                f.write(f'{year}-{month}: {e}\n')
            sleep(20)
