from PIL import Image
import numpy
from numpy import linalg
from numpy import array


# Lossy image compression using SVD
class ImageCompression:
    # Degree of precision we want
    modes = 750

    # Initializes filename and creates PIL image
    def __init__(self, filename):
        self.image_loc = filename
        self.img = Image.open(filename)

    # Compresses the image
    def compress(self, modes=750):
        self.modes = modes
        # Split the image into RGB channels
        red, green, blue = Image.Image.split(self.img)

        # Get the compressed channels
        red_comp = self.svd(red)
        grn_comp = self.svd(green)
        blue_comp = self.svd(blue)

        # Get image as array, set the individual channels to our compressed versions
        arr = array(self.img)
        arr[:, :, 0] = red_comp
        arr[:, :, 1] = grn_comp
        arr[:, :, 2] = blue_comp

        # Create image, overwriting the original
        img = Image.fromarray(arr)
        img.save(self.image_loc)

    # Helper method to compress a channel
    def svd(self, channel):
        # Convert to matrix
        img_mat = numpy.matrix(array(channel))

        # Perform Singular Value Decomposition on our matrix
        u, sigma, v = linalg.svd(img_mat)

        # We want to keep n cols of u, n numbers in the diagonal of sigma, and n rows of v
        # Then we multiply them together to get the compressed image, and return that as a matrix
        return numpy.matrix(u[:, :self.modes]) * numpy.diag(sigma[:self.modes]) * numpy.matrix(v[:self.modes, :])
