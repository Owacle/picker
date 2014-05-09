
import maya.cmds as cmds

class Button():
    '''
    just really a container for the button data, like colour and icon and position
    doesn't have any specific logic so doesn't need to extend the maya one yet
    '''
    
    def __init__(self, label, top, left, height, width, bgcol, command, items):
        '''

        '''
        self._label = label
        self._left = left
        self._top = top
        self._height = height
        self._width = width
        self._colour_base = bgcol
        #will use this later
        self._colour_over = [0.8,0.8,0.4]
        self._colour_selected = [0.9,0.3,0.3]
        self._command = command
        self._items = items

    def __str__(self):
        '''
        the string representation of the button class
        '''
        return '<Btn:%s [%s,%s] %sx%s [%1.1f,%1.1f, %1.1f] cmd:%s items:%s>' % (self._label, 
                                                                self._top, 
                                                                self._left, 
                                                                self._height, 
                                                                self._width, 
                                                                self._colour_base[0],self._colour_base[1],self._colour_base[2],
                                                                self._command,
                                                                self._items)
                
    def get_name(self):
        return self._label

    def get_position(self):
        '''
        returns the position 
        - format: [left, top]
        '''
        return [self._left, self._top]

    def get_size(self):
        '''
        returns the size
        - format: [width, height]
        '''
        return [self._width, self._height]

    def get_left(self):
        return self._left

    def get_top(self):
        return self._top

    def get_height(self):
        return self._height

    def get_width(self):
        return self._width

    def get_bgcol(self):
        return self._colour_base

    def get_bgcol_str(self):
        colour_string = '[%1.1f,%1.1f,%1.1f]' % (self._colour_base[0],self._colour_base[1],self._colour_base[2])
        return colour_string

    def get_command(self):
        return self._command

    def get_min_max(self, item):

        start = item.find('[')
        mid = item.find('|')
        end = item.find(']')

        if start>0:

            return [str(item)[start+1:mid], str(item)[mid+1:end]]
            # print item[:start] + ' - ',
            # print str(item)[start+1:mid] + '|',
            # print str(item)[mid+1:end]
        else:
            return None

    def get_items(self):
        '''
        returns the actual items, not a string
        '''
        return self._items

    def get_item_only(self, item):
        '''
        return the item without any min/max or value bits at the end
        '''
        #print item     
        bracket = item.find('[')
        equal = item.find('=')
        plus = item.find('+')
        minus = item.find('-')
        if bracket > 0:
            return str(item)[:bracket]
        elif equal > 0:
            return str(item)[:equal]
        elif plus > 0:
            return str(item)[:plus]
        elif minus > 0:
            return str(item)[:minus]
        else:
            return str(item)

    def get_items_string(self):
        items_string = ''
        for item in self._items:
            start = item.find('[')
            if start > 0:
                items_string += str(item)[:start] +','
            else:
                items_string += str(item) +','
        return items_string[:-1]


class ButtonGroup():
    '''
    A group of buttons which I'll use to make the tweak buttons
    '''
    def __init__(self):
        pass