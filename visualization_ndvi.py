# importing libraries
import cartopy.feature as cf
import cartopy.crs as ccrs
import xarray as xr
import matplotlib.pyplot as plt
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import geopandas as gpd
import numpy as np
import matplotlib.colors as colors
import matplotlib.colorbar as colorbar
from matplotlib.colors import LinearSegmentedColormap
import os
import glob
from PIL import Image
import gc

# defining the functions

def mode(x, axis):
    val, cnt = np.unique(x, return_counts=True)
    return val[np.argmax(cnt)]

def filepath(month):
    return f'F:/daten_rese_task2/bumba_NDVI_{month}.nc'

def load_data(month):
    try:
        data = xr.open_dataset(filepath(month)).rename(dict(x='lon', y='lat', t='time'))
        data.attrs = {'long_name': 'NDVI', 'units': '-'}
        
    except FileNotFoundError:
        data = None
    
    return data

def load_combined_data(months):
    data = xr.concat([load_data(month) for month in months if load_data(month) is not None], dim='time')
    return data

def process_data(data, sample_bands = [4, 5]):
    return data['NDVI'].where(data['SCL'].isin(sample_bands), np.nan).mean(dim=['time'])

def reclassify_difference(difference, threshold):
    reclassed = difference * 0.0
    reclassed = xr.where(difference >= threshold, 1, reclassed)
    reclassed = xr.where(difference <= -threshold, -1, reclassed)
    return reclassed

def before_after(beginning_index, window_size=2, available_data=available_data, threshold=0.1):
    month_before = available_data[beginning_index : beginning_index + window_size]
    month_after = available_data[beginning_index +  window_size : beginning_index + 2*window_size]

    data_before = process_data(load_combined_data(month_before))
    data_after = process_data(load_combined_data(month_after))
    difference = reclassify_difference(data_after - data_before, threshold)

    title_before = f"Average NDVI {month_before[0]} - {month_before[-1]}"
    title_after = f"Average NDVI {month_after[0]} - {month_after[-1]}"
    title_difference = f'NDVI Change (|NDVI| ≥ {threshold})'

    return data_before, data_after, difference, title_before, title_after, title_difference

def beautify_ax(ax, title):

    # Set up gridlines and format them to display longitude and latitude labels
    gl = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)
    gl.top_labels = False
    gl.right_labels = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER

    # Set title
    ax.set_title(title)

def plot_pair(beginning_index, window_size, threshold=0.1, path = None):
    before, after, difference, title_before, title_after, diff_title = before_after(beginning_index = beginning_index, window_size = window_size, threshold=threshold)

    # Create subplots
    fig, axs = plt.subplots(1, 3, figsize=(12, 4), subplot_kw=dict(projection=ccrs.UTM(zone='34')), sharey=True, sharex=True)

    colors = ['tab:red', 'lightgray', 'tab:blue']
    cmap = LinearSegmentedColormap.from_list("myColormap", colors)

    # Call the function for each subplot
    for i, (x, title) in enumerate(zip([before, difference, after], [title_before, diff_title, title_after])):
        ax = axs[i]
        if i != 1:
            im = x.coarsen(lat=5, lon=5, boundary='trim').mean().plot(cmap='viridis', vmin=0.2, vmax=0.9, add_colorbar=False, ax=ax)
            cbar = plt.colorbar(im, shrink= 0.7, label='', orientation='horizontal')
            # cbar.ax.set_yticklabels(['Decrease', 'Increase'], rotation=90, verticalalignment='center')
        else:
            # im = x.coarsen(lat=5, lon=5, boundary='trim').mean().plot(cmap='coolwarm', add_colorbar=False, ax=ax)
            im = x.coarsen(lat=5, lon=5, boundary='trim').mean().plot.contourf(cmap=cmap, levels=[-1, -0.1, 0.1, 1], add_colorbar=False, ax=ax)
            cbar = plt.colorbar(im, shrink= 0.7, ticks=[-0.55, 0, 0.55], label='', orientation='horizontal')
            cbar.ax.set_xticklabels(['Decrease', 'Steady', 'Increase'])
        beautify_ax(ax, title)

    plt.tight_layout()

    if path is not None:
        
        filename = f'{path}/plot_w{window_size}_t{threshold}_{title_before[13:19]}.png'
        plt.savefig(filename, dpi=300)
        plt.close()
    
    else:
        plt.show()

def make_gif(frame_folder, gifname):
    frames = [Image.open(image) for image in glob.glob(f"{frame_folder}/*.png")]
    frame_one = frames[0]
    frame_one.save(gifname, format="GIF", append_images=frames,
               save_all=True, duration=1000, loop=0)

def run_all(window_size, threshold=0.2, save = False, early_stop = False):
    if save:
        path = f'./plots/frames_w{window_size}_t{threshold}'

        suggsess = False
        while suggsess is not True:
            try:
                os.makedirs(path)
                suggsess = True
            except FileExistsError:
                path = path + '_new'
    else:
        path = None
    
    if early_stop is False:
        stop_index = len(available_data) - (2*window_size + 1)
    else:
        stop_index = early_stop

    for i in range(0, stop_index):
        plot_pair(beginning_index = i, window_size = window_size, threshold=threshold, path = path)
    
    gifname = f'{path}/animation_w{window_size}_t{threshold}.gif'

    make_gif(frame_folder=path, gifname=gifname)

# running the script
if __name__ == '__main__':

    # defining the available extent
    available_data = [year * 100 + month for year in range(2017, 2024) for month in range(1, 13)]

    # looping through the window sizes and thresholds
    for window_size in range(2, 5):
        for threshold in range(1, 6):
            print(f'Running window size {window_size} and threshold {threshold/10}')
            run_all(window_size = window_size, threshold = threshold/10, save=True, early_stop=False)
            gc.collect()