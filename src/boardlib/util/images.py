import os
from PIL import Image

def overlay_images(base_dir, image_paths, output_filepath):
    """
    Creates an overlayed image of an entire board layout from the various hold-set images.
    Assumes that all input images are from the same layout+product_size and are thus compatible for a raw overlay.
    
    :param base_dir: The base directory.
    :param image_paths: The list of image paths for each layout image.
    :param output_filepath: The final filepath to which to save the overlayed images.
    """    
    images = [Image.open(f"{base_dir}/{image_path}").convert("RGBA") for image_path in image_paths]

    canvas = Image.new("RGBA", (images[0].width, images[0].height), (0, 0, 0, 0))

    for img in images:
        canvas.paste(img, mask=img)

    output_dir = os.path.dirname(output_filepath)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    canvas.save(output_filepath, "PNG")