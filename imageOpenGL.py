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
#
# ImageOpenGL
# Attempts to import PyOpenGL, open a window for OpenGL rendering,
# and enter the glut render loop.  If that succeeds, the class can
# be used to accumulate pixels in an OpenGL texture and display that
# texture in the window.  A callback function is supplied as an argument
# to the function that enters the render loop, so users of this class
# can register a function that will be called once per trip through 
# the glut render loop.
#

import sys, time, cProfile
from array import array
import params
from imageBase import ImageBase

# If profiling, hit 'ESC' in the gl window to exit and display
# profile information.  Exiting by clicking the window's close
# button will not display the profile information.

runProfile = False

class ImageOpenGL(ImageBase):
    def __init__(self):
        ImageBase.__init__(self)

        self.prof = None
        if runProfile:
            self.prof = cProfile.Profile()
            self.prof.enable()

        self.glutWindow = None

        # The aspect ratio of a pixel on a computer is different
        # from what it is on an NTSC standard def television.  We
        # could display each pixel from the simulation as a single
        # pixel on your screen, but this would display a tall skinny
        # image.  To do that, use these commented-out lines:
        #self.windowWidth = params.scanlineNumPixels
        #self.windowHeight = params.frameHeightPixels * 2
        # Instead, we stretch each pixel horizontally.  Each pixel
        # of the simulation covers three pixels in the vertical 
        # direction.
        self.windowWidth = int(params.scanlineNumPixels * 4)
        self.windowHeight = int(params.frameHeightPixels * 3)

        self.textureId = None
        self.startedNewImage = True
        self.renderToTopHalf = True

        self.initOpenGL()

        glClearColor(1, 1, 1, 0.0)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glEnable(GL_TEXTURE_2D)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
        glClear(GL_COLOR_BUFFER_BIT)
        glutSwapBuffers()
        glClear(GL_COLOR_BUFFER_BIT)

    def glutcb_display(self):
        """ Draws the image as the simulation runs """

        #print('display for last %d, %d'%(self.lastPixelX, self.lastPixelY))

        self.perRenderCallback()

        # We bound the texture in initOpenGL() and for the 6502 + TIA
        # simulation, all the OpenGL rendering is in this module, so
        # no need to unbind it or reset the OpenGL state.
        #
        # Render a quad covering half the window.  We show alternate
        # frames in alternate halves of the window.
        # Yeah - using silly immediate mode, but this is called every few
        # seconds after hundreds of pixels have been computed, so performance
        # doesn't matter, and I'm too lazy to make a buffer.

        # change the geom to render to alternate halves of the window
        y = -1
        if self.renderToTopHalf:
            # 0.005 to leave a little gap between upper and lower images
            y = 0.005

        glBegin(GL_TRIANGLE_STRIP)
        glTexCoord2f(0, 0)
        glVertex2f(-1,  y + 1)
        glTexCoord2f(0, 1)
        glVertex2f(-1,  y + 0)
        glTexCoord2f(1, 0)
        glVertex2f( 1,  y + 1)
        glTexCoord2f(1, 1)
        glVertex2f( 1,  y + 0)
        glEnd()
        
        glutSwapBuffers()
        glutPostRedisplay()

    def glutcb_keyboard(self, key, winx, winy):
        if ord(key) == 27:   # ESCAPE  \033
            print('ESC pressed: Quitting')
            if self.prof != None:
                print('Writing profiler report')
                self.prof.create_stats()
                self.prof.print_stats(sort = 1)  # -1 to not sort
                fileName = 'profile_%s'%(time.strftime('%y_%m%d_%H%M%S'))
                self.prof.dump_stats(fileName)

            glutDestroyWindow (self.glutWindow)
            #glutLeaveMainLoop()
            print('Done')

    def initOpenGL(self):
        args = [sys.argv[0]]
        glutInit(args)
        glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH | GLUT_STENCIL)
        glutInitWindowSize(self.windowWidth, self.windowHeight)
        glutInitWindowPosition(30, 30)
        windowTitle = 'Transistor-level simulation of an Atari 2600'
        self.glutWindow = glutCreateWindow(windowTitle)
        glutDisplayFunc(self.glutcb_display)
        glutKeyboardFunc(self.glutcb_keyboard)

        self.textureId = glGenTextures(1)
        # TODO: checkGL()
        glBindTexture(GL_TEXTURE_2D, self.textureId)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        self.clearTexture(0xFFFFFFFF)

    def clearTexture(self, intRGBA):
        glBindTexture(GL_TEXTURE_2D, self.textureId)

        # To set all pixels black:
        # imageStr = '\0'*(self.getNumPixels() * 4)
        # To set all pixels to the given RGBA color, 8 bits per component:
        # 'B' for unsigned byte
        a = array('B', self.rgbaIntToList(intRGBA) * self.getNumPixels())
        imageStr = a.tostring()

        glTexImage2D(GL_TEXTURE_2D,    # target
                     0,                # mipmap level
                     GL_RGBA,          # internal format
                     self.imageWidth,
                     self.imageHeight,
                     0,                # border
                     GL_RGBA,          # source format
                     GL_UNSIGNED_BYTE, # source type
                     imageStr)
        
    def restartImage(self):
        if self.lastPixelY > params.frameHeightPixels * 0.7:
            self.renderToTopHalf = not self.renderToTopHalf
        self.lastPixelX = 0
        self.lastPixelY = 0
        self.clearTexture(0xFFFFFFFF)
             
    def enterRenderLoop(self, funcCallbackPerRender):
        self.perRenderCallback = funcCallbackPerRender
        # Enter the OpenGL disply loop, which will call the callbacks
        # we registered in initOpenGL() and not return until the window
        # is closed or something causes the loop to end.
        glutMainLoop()

    # TODO: group pixels into scanlines, and scanlines into rectangular
    # regions to update with a single call to glTexSubImage, rather than 
    # calling it for each pixel
    #
    def setPixel(self, x, y, rgbaInt):
        #print('ImageOpenGL setPixel(%d, %d, 0x%8.8X)'%(x, y, rgbaInt))
        # TODO: detect if wrapped around and switch region?
        # TODO: update gl texture
        if x == 0 and y == 0:
            self.startedNewImage = True

        a = array('B', self.rgbaIntToList(rgbaInt))  # 'B' for unsigned byte
        astr = a.tostring()

        glBindTexture(GL_TEXTURE_2D, self.textureId)
        glTexSubImage2D(GL_TEXTURE_2D,    # target
                        0,                # mipmap level
                        x, y,             # offset into texture
                        1, 1,             # width, height of subimage
                        GL_RGBA,          # format
                        GL_UNSIGNED_BYTE, # type
                        astr)

def getInterface():
    try:
        import OpenGL
        import OpenGL.GL as gl
        import OpenGL.GLUT as glut

        # Doing 'from OpenGL.GL import *' does not import to 
        # this module's namespace, so go over the module's
        # __dict__ contents and add them to this module's
        # globals()

        globalDict = globals()
        for key in gl.__dict__:            
            if key not in globalDict:
                globalDict[key] = gl.__dict__[key]

        for key in glut.__dict__:
            if key not in globalDict:
                globalDict[key] = glut.__dict__[key]

        print('Done importing OpenGL.  A window should appear to show ' +
              'pixels and image frames')

    except RuntimeError as err:
        print('RuntimeError {0}: {1}'.format(err.errno. err.strerror))
        print('Could not import PyOpenGL.  Will not display pixels and frames')
        return None

    return ImageOpenGL()
