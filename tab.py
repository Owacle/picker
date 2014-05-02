
import button

class Tab():
    '''
    a Holder for the individual buttons on the picker
    '''

    def __init__(self, title, bgimage):
        self._title = title
        self._buttons = []
        self._bgimage = bgimage
        print 'making a new tab called %s' % (self._title)

    def __str__(self):
        full_list = ''
        for button in self._buttons:
            full_list += '   .  ' + str(button)[:20] + '\n'
        return 'TAB: %s \n  -  Buttons: \n%s' % (self._title, full_list)

    def get_title(self):
        return self._title

    def get_image_string(self):
        return self._bgimage

    def add_button(self, extra_button):
        self._buttons.append(extra_button)

    def all_buttons(self):
        return self._buttons
        
