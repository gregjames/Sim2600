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
#------------------------------------------------------------------------------

import params

class ImageBase():
    def __init__(self):
        self.imageWidth  = params.scanlineNumPixels
        self.imageHeight = params.frameHeightPixels 

        # Last pixel that was updated
        self.lastPixelX  = 0
        self.lastPixelY  = 0

    def getNumPixels(self):
        return self.imageWidth * self.imageHeight

    def setPixel(self, x, y, rgbaInt):
        pass

    def setNextPixel(self, rgba):
        #print('ImageBase setNextPixel(0x%8.8X) %d %d'%
        #      (rgba, self.lastPixelX, self.lastPixelY))
        self.setPixel(self.lastPixelX, self.lastPixelY, rgba)
        self.lastPixelX += 1
        if self.lastPixelX >= self.imageWidth:
            self.startNextScanline()

    def startNextScanline(self):
        self.lastPixelX = 0
        self.lastPixelY += 1
        if self.lastPixelY >= self.imageHeight:
            self.lastPixelY = 0
        
    def rgbaIntToList(self, rgbaInt):
        return [(rgbaInt >> 24) & 0xFF,
                (rgbaInt >> 16) & 0xFF,
                (rgbaInt >> 8)  & 0xFF,
                (rgbaInt)       & 0xFF]
