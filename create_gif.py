import glob
from PIL import Image

def make_gif(frame_folder, gifname):
    frames = [Image.open(image) for image in glob.glob(f"{frame_folder}/*.png")]
    frame_one = frames[0]
    frame_one.save(gifname, format="GIF", append_images=frames,
               save_all=True, duration=1000, loop=0)