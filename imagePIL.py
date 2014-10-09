# Copyright (c) 2014 Greg James, Visual6502.org
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os, time
from imageBase import ImageBase
import params

Image = None

class ImagePIL(ImageBase):
    def __init__(self):
        print('Creating ImagePIL class to save frame images')
        ImageBase.__init__(self)
        self.image = Image.new("RGBA", (params.scanlineNumPixels,
                                        params.frameHeightPixels), "white")
        self.outputDir = params.imageOutputDir
        self.frameCount = 0
        self.dateTimeStr = time.strftime('%y_%m%d_%H%M%S')


    def setPixel(self, x, y, rgba):
        rgbaTuple = ((rgba >> 24) & 0xFF, (rgba >> 16) & 0xFF,
                     (rgba >> 8) & 0xFF, rgba & 0xFF)

        # For the other endianness:
        #rgbaTuple = (rgba & 0xFF, (rgba >> 8) & 0xFF,
        #             (rgba >> 16) & 0xFF, (rgba >> 24) & 0xFF)

        #print('ImagePIL setPixel(%d, %d, 0x%8.8X) tup %s'%
        #       (x, y, rgba, str(rgbaTuple)))

        self.image.putpixel((x,y), rgbaTuple)

    def restartImage(self):
        # Save if we've got more than 80% of a frame
        if self.lastPixelY >= params.frameHeightPixels * 0.8:
            fileName = 'frame_%s_%4.4d.png'%(self.dateTimeStr, self.frameCount)
            filePath = self.outputDir + '/' + fileName
            print('Saving frame %d image to %s'%(self.frameCount, filePath))
            self.image.save(filePath)
            self.frameCount += 1
        self.lastPixelX = 0
        self.lastPixelY = 0

def getInterface():
    global Image
    # If we can't import the Python Image Library (PIL), return None
    try:        
        from PIL import Image as Image
    except:
        print('Could not import Python Image Library.  Will not save .png images')
        return None

    try:
        if not os.path.exists(params.imageOutputDir):
            os.makedirs(params.imageOutputDir)
    except:
        print('Could not create output directory for frame images')
        return None

    return ImagePIL()

