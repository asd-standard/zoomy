## PyZUI 0.1 - Python Zooming User Interface
## Copyright (C) 2009  David Roberts <d@vidr.cc>
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
## 02110-1301, USA.

"""Strings to be displayed in the ZUI."""

#from threading import Thread
from PyQt5 import QtCore, QtGui

from .mediaobject import MediaObject, LoadError, RenderMode

class StringMediaObject(MediaObject): #, Thread
    """
    StringMediaObject['MediaObject']

    Constructor : 
        StringMediaObject(string, scene)
    Parameters :
        media_id['string'], scene['Scene']

    StringMediaObject(media_id, scene) --> None

    StringMediaObject objects are used to represent strings that can be
    rendered in the zui"

    `media_id` should be of the form 'string:rrggbb:foobar', where 'rrggbb' is
    a string of three two-digit hexadecimal numbers representing the colour of
    the text, and 'foobar' is the string to be displayed.
    """
    def __init__(self, media_id, scene):
        
        MediaObject.__init__(self, media_id, scene)
        hexcol = self._media_id[len('string:'):len('string:rrggbb')]
        self.__color = QtGui.QColor('#' + hexcol)
        if not self.__color.isValid():
            raise LoadError("the supplied colour is invalid")
        
        self.__str = self._media_id[len('string:rrggbb:'):] 

        self.lines = []
        self.lines.append([])
        
        # in order for a multi line string to be rendered of the exact size self.lines have to be 
        # set to the right value before self.onscreen_size method gets called
        '''
        cdef char* c_str = self.__str
        j=0
        i=0
        while c_str[i] != 0:
            if c_str[i] == 10:  # ASCII value of '\n'
                self.lines.append([])
                j += 1
            else:
                self.lines[j].append(c_str[i].decode('ascii'))  # convert char to Python str
            i += 1
            #gives error, expected bytes, str found
        '''
        j=0
        for i in list(self.__str) :  
                # If a \n char is encountered a new sublist is appended to self.lines              
                if i == '\n' :                    
                    self.lines.append([])
                    j += 1
                else :
                # Otherwise the char is appended to the currend self.lines sublist
                    self.lines[j] += str(i)
        
        


    transparent = True

    ## point size of the font when the scale is 100%
    base_pointsize = 24.0

    def render(self, painter, mode):
        '''Given QtPainter and Rendering mode renders the string calculating the 
           rendering rectangle and using QtPainter.DrawText
        '''
        
        if min(self.onscreen_size) > int((min(self._scene.viewport_size))/44) and \
        max(self.onscreen_size) < int((max(self._scene.viewport_size))/1.3) and mode \
        != RenderMode.Invisible:
            ## don't bother rendering if the string is too
            ## small to be seen, or invisible mode is set
            
            painter.setPen(self.__color)
            painter.setFont(self.__font)
            
            # Broke the string in a characters list     
            
            x,y = self.topleft
            w,h = self.onscreen_size 
            font = self.__font   
         
            if font:
                fontmetrics = QtGui.QFontMetrics(font)
            hl = fontmetrics.height()
                     
            
            if len(self.lines) > 1 :
                yr = y                
                rectlist = []
                
                for i in range(len(self.lines)) :
                    '''for every line in self.lines a QRectF is created below the previous one 
                    for the line to be painted on by QtPainter.drawText method
                    '''
            
                    rectlist.append(QtCore.QRectF(int(x), int(yr), int(w), int(hl)))
                    yr += hl  
       
                    #print(self.lines[i]) #, type(self.lines[i])
                    if i < (len(self.lines)-1) :                
                        string = ''.join(self.lines[i][:])
                    else :
                        string = ''.join(self.lines[i][:])
    
                    rect = rectlist[i]
                    painter.drawText(rect, string) 
 
            else :
                rect = QtCore.QRectF(int(x), int(y), int(w), int(hl))
                string = ''.join(self.lines[0])                
                painter.drawText(rect, string ) #, QtCore.Qt.AlignCenter

           
            


    @property
    def __pointsize(self):
        return self.base_pointsize * self.scale


    @property
    def __font(self):
        pointsize = self.__pointsize
        if pointsize < 1:
            ## too small to be seen
            return None

        font = QtGui.QFont('Sans Serif')
        font.setPointSizeF(pointsize)
        return font


    @property
    def onscreen_size(self):
        '''Returns with and height of the MediaObject passed to the StringMediaObject Class
        '''
        font = self.__font

        if font:
            fontmetrics = QtGui.QFontMetrics(font)
            
            if len(self.lines) > 1 :
                # Returns the width of the longest line in the paragraph stack.
                w = fontmetrics.width(''.join(sorted(self.lines, key=len, reverse=True)[0][:])+'-------')         
                # Returns the font height times the number of lines in the paragraph stack                
                h = fontmetrics.height()*len(self.lines)
                
            else :
                # Is the sting is not a paragraph just gives the lenght of the string 
                w = fontmetrics.width(self.__str+'-')
                # and the height of the font
                h = fontmetrics.height()                
            return (w,h)

        else:
            return (0,0)


