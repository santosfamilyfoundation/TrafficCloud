import os
from fpdf import FPDF
from PIL import Image

def makePdf(pdfFileName, listImages, dir = ''):
    """
    Arguments
    ---------
    pdfFileName: str, i.e. 'output'
    listImages: list of str, i.e. ['road_user_type_counts.png', 'speed_cdf.png']
    dir: str, path where images located, and pdf will be outputted
    """
    cover = Image.open(os.path.join(dir, listImages[0]))
    width, height = cover.size

    pdf = FPDF(unit = "pt", format = [width, height])

    # Save an image per page
    for page in listImages:
        pdf.add_page()
        pdf.image(os.path.join(dir,str(page)), 0, 0)

    pdf.output(os.path.join(dir, pdfFileName, ".pdf"), "F")

