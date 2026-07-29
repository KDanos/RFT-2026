from PyQt6.QtCore import Qt, QRect, QSize
from PyQt6.QtGui import QIcon, QPainter
from PyQt6.QtWidgets import QHeaderView

from ui.filterable_table.filter_by_row_menu import FilterByRowMenu
from ui import app_icon

class FilterableHeaderView(QHeaderView):
    """Horizontal header that reserves space for a small filter icon"""

    #Define icon sizes, to make adjustments easier
    ICON_SIZE = 14  #  icon square size, in pixels
    ICON_MARGIN = 4 # gap between icon and the section's right edge

    def __init__(self, orientation:Qt.Orientation, parent = None)->None:
        super().__init__(orientation, parent)
        # self.filter_icon:QIcon = app_icon("fa5s.filter")
        self.filter_icon:QIcon = app_icon("mdi.filter-menu")

    def icon_rect (self, section_rect:QRect) ->QRect:
        """ Icon_rect takes a QRect a argument, representing the whole header section.
            It returns a new QRect, representing the small area of the filter icon inside the header section.
            The returned rectangle is in the same coordinate system as the input QRect
            Reserved for the icon and pinned to the right edge of the section and vertically centered.
        """
        size = self.ICON_SIZE
        x = section_rect.right() - self.ICON_MARGIN - size
        y = section_rect.top() + (section_rect.height()-size)//2
        return QRect(x , y, size, size) 
    
    def paintSection(self, painter:QPainter, rect:QRect, logicalIndex:int)->None:
        #First the original, built-in implementation, before applying changes in the next lines
        super().paintSection(painter, rect, logicalIndex)
        
        #Create a new QRect object to sit inside the QRect assigned to the header
        icon_rect = self.icon_rect(rect)
        self.filter_icon.paint(painter, icon_rect)  

    def sectionSizeFromContents(self, logicalIndex: int) -> QSize: 
        # This is what QHeaderView.sectionSizeHint()/resizeColumnsToContents()
        # actually consult - widen the default content size so the reserved
        # icon strip is extra space, not stolen from the text.
        size = super().sectionSizeFromContents(logicalIndex) 
        extra = self.ICON_SIZE + (self.ICON_MARGIN * 2)
        return QSize(size.width() +  extra, size.height())
        
    def mousePressEvent(self, event)->None: 
        pos = event.position().toPoint() 
        #Return the column index where the mouse has been pressed
        logical_index = self.logicalIndexAt(pos.x()) 

        if logical_index >=0: 
            #Create a rectangle representing the position and dimensions of the clicked header
            section_rect = QRect(
                self.sectionViewportPosition(logical_index),
                0,
                self.sectionSize(logical_index), 
                self.height(),
            ) 

            #Recompute the filter icon in header-local coordinates
            current_filter_icon = self.icon_rect(section_rect)
            if current_filter_icon.contains(pos):
                #Convert from local (i.e. icon rect corner from header poistion to global screen coordinates)
                global_pos = self.mapToGlobal(current_filter_icon.bottomLeft())            
                #Call the filtering menu
                menu = FilterByRowMenu(logical_index)
                menu.exec(global_pos)
                # Swallow the event and do not proceed to default mousePress event bahaviour (e.g. resize sort columns)
                return 
        
        #Restore the original mousePressEvent functionality (e.g. resize sort columns)
        super().mousePressEvent(event)

