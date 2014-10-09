#!/bin/bash

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

sudo apt-get install -y build-essential
sudo apt-get install -y freeglut3 freeglut3-dev
sudo apt-get install -y python-dev python-pip python-imaging

# With PyOpenGL, we'll render pixels to a window as the 
# simulation progresses
sudo pip install PyOpenGL

# With PIL (import Image), we'll save image frames to disk as
# each is completed.  Note 'pip install Image' is not what we want.
#sudo pip install pil
#sudo pip install Pillow

