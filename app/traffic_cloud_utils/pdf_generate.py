import os
from fpdf import FPDF
from PIL import Image

def makePdf(out_path, listImages, dir = ''):
    """
    Arguments
    ---------
    out_path: str, i.e. 'path/to/output.pdf'
    listImages: list of str, i.e. ['road_user_type_counts.png', 'speed_cdf.png']
    dir: str, path where images located, and pdf will be outputted
    """

    pdf = FPDF(orientation='L', unit = "in", format = 'Letter')

    # Save an image per page
    for page in listImages:
        pdf.add_page()

        img_path = os.path.join(dir,str(page))
        img = Image.open(img_path)
        w, h = img.size
        
        # all images default 8 inch width
        width = 8

        # height in inches, relative to aspect ratio
        height = width * (h // w)

        pdf.image(img_path, x=1, y=1, w=width, h=height)

    pdf.output(out_path, "F")

