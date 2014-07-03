'''
Melt's mega picker
 ver 0.5
 started around 1 October 2013
 last update: Tuesday 11 2014

TODO:
0. Class structure
10. Select all button
20. Look into drag selection (probably not feasible in a gui)
30. Selection highlighting
40. Add/Remove/Edit buttons

'''

import maya.cmds as cmds
from pymel.core import * # for the file handling
import os
import xml.etree.ElementTree as ET
from tab import *
from button import *

class Picker():
    '''
    A simple GUI picker using an external text file
    Author: Melt van der Spuy
    '''

    # Namespace holder
    _namespace = ''
    # The items that are selected (possibly update this dynamically)
    _selection = []
    # The character name (could be different to the namespace)
    _who = []
    # tweak amount to start with
    _tweak = 0.1
    _brow_attribs = ["Brow_Blend_Ctrl.BrowInOut",
                     "Brow_Blend_Ctrl.BrowUpDown",
                     "Brow_Blend_Ctrl.Brow_Squeeze_",
                     "Brow_Blend_Ctrl.Brow_Sad_",
                     "Brow_Blend_Ctrl.Brow_Worried_",
                     "Brow_Blend_Ctrl.Brow_Angry_",
                     "Brow_Blend_Ctrl.Brow_Surprised_"]
    _eye_attribs = ["R_Eye_Transform.upperEyeLidBlink"]
    _mouth_attribs = ["Mouth_Blend_Ctrl.Smile_L",
                      "Mouth_Blend_Ctrl.Frown_L",
                      "Mouth_Blend_Ctrl.Sneer_L",
                      "Mouth_Blend_Ctrl.MouthCornerL",
                      "Mouth_Blend_Ctrl.Mouth_Pull",
                      "Mouth_Blend_Ctrl.Cheek_Puff_L",
                      "Mouth_Blend_Ctrl.Phoneme_Ee_L",
                      "Mouth_Blend_Ctrl.Phoneme_FV",
                      "Mouth_Blend_Ctrl.Phoneme_Oo",
                      "Mouth_Blend_Ctrl.Phoneme_BMP",
                      "Mouth_Blend_Ctrl.Smile_Toothy",
                      "Mouth_Blend_Ctrl.Phoneme_Oh"]
    # list of the sliders controlling the face attribs which we need to connect when WHO changes
    _face_sliders = []
    # the currently selected tab
    _tab = ''
    # The main scene name space for purposes of getting the selection accurately
    _scene_name = ''
    # the name of the window - will likely be over-written by the button file
    _window_title = 'Melt Picker'
    # the current directory that we were loaded from (for getting images and icons etc)
    _pwd_base = ''
    _pwd_icn = '/icons/'
    _pwd_img = '/images/'
    # the original lines from the file
    _all_lines = []
    _all_buttons = []
    # the size of the picker window - we set a default but we can over ride in the button file
    _window_width = 350
    _window_height = 470
    _who_buttons = []
    _extra_buttons = []

    #size of the bottom bits
    _EXTRA_HEIGHT = 76
    _WHO_HEIGHT = 40

    _WHO_BUTTON_COLOUR_BASE = [0.3,0.3,0.3]
    _WHO_BUTTON_COLOUR_SELECTED = [0.95,0.3,0.3]

    _debug = False

    # _tab1 = [name1, button1, button2]
    # _tab2 = [name2, button3, button4]
    # _controls = [_tab1, _tab2]

    def __init__(self):
        display_string = 'the window is ' + str(self._window_width) + 'px wide and '  + str(self._window_height) + 'px high'
        #setting the directory stuff and file name etc
        self._tabs_list = []
        self._pwd = os.path.dirname(__file__)
        self._buttons_file = '/buttonListVeg_v15.txt'
        self._controls_list = self.load_buttons()
        self._the_who_list = self.get_char_names()
        #print display_string

    def num_tabs(self):
        total = 0
        try:
            total += len(self._tabs_list)
            #print ' we got more'
        except:
            print 'exception'
            pass
        return total

    def modifier_pressed(self):
        '''
        return the string associated with the currently held modifier key
        '''
        mods = cmds.getModifiers()
        return_list = []
        if (mods & 1) > 0: return_list.append('SHIFT')
        if (mods & 2) > 0: return_list.append('CAPSLOCK')
        if (mods & 4) > 0: return_list.append('CONTROL')
        if (mods & 8) > 0: return_list.append('ALT')

        return return_list

    def get_char_names(self):
        '''
        returns the list of the characters
        '''

        all_char = []

        all_children = cmds.namespaceInfo(':', listOnlyNamespaces=True)
        for inner in all_children:
            if 'VGT' in inner:
                    all_char.append(inner)

        if len(all_char) == 0:
            all_char = ['_none', '1_more']
        return all_char

    def set_who(self, new_who_id):
        def set_who_sub(*args):
            '''
            Changes the current active character for the picker
            '''

            #get the who from within the ID

            tab = new_who_id.split('|')[:-1]
            new_who = new_who_id.split('|')[-1]
            mods = self.modifier_pressed()

            #shift adds it to the selection
            if 'SHIFT' not in mods:
                #could find the right one, but lets just set ALL the buttons to the default
                for each_who_button in self._who_buttons:
                    cmds.button(each_who_button, edit=True, backgroundColor=self._WHO_BUTTON_COLOUR_BASE)
                self._who = []

            #now set the colour for the selected one
            cmds.button(new_who_id, edit=True, backgroundColor=self._WHO_BUTTON_COLOUR_SELECTED)
            if new_who not in self._who:
                self._who.append(new_who)
            #print self._who

            self.connect_face()
        return set_who_sub

    def do_select(self, item_list):
        def do_select_sub(*args):
            # "*args" is still required because this is the
            # function that Maya will ultimately call when
            # the button is pushed
            print item_list
            fullname_list = []
            skip_list = []
            #this is purely for feedback purposes
            pick_list = []
            for the_who in self._who:
                print the_who

                #check who once at the top so its not being checked for every object
                if the_who != 'none':
                    suffix = the_who + ":"
                else:
                    suffix = ''

                for ctrl in item_list:
                    # a check to see if something exists in the list of controls more than once
                    if(item_list.count(ctrl)>1):
                        print ctrl

                    # adding the name of the character to the control to get a full selection name
                    # *** should probably do this when we make the command so its done once and then we can just do it
                    fullName = str(suffix + ctrl)
                    if cmds.objExists(fullName):
                        #print 'not skipping: '+fullName
                        # double checking that we dont already have it in the list - so we can't SHIFT select an item thats already selected
                        if(fullName not in fullname_list):
                            fullname_list.append(fullName)
                            pick_list.append(ctrl)
                    else:
                        #print 'skipped: '+ ctrl
                        skip_list.append(ctrl)
                # else:
                #   fullname_list = item_list[:]
                #   print fullname_list


            if len(fullname_list)>0:
                try:
                    mods = self.modifier_pressed()

                    if 'SHIFT' in mods:
                        #for checkMe in fullname_list:
                        #if cmds.objExists(checkMe):
                        cmds.select(fullname_list, add=True)
                        #   print 'added:', pick_list
                        #else:
                        #   print 'skipped: '+checkMe
                    elif 'CONTROL' in mods:
                        cmds.select(fullname_list, tgl=True)
                        #print 'toggled:', pick_list
                    else:
                        # for each in fullname_list:
                        #   print fullname_list.count(each)
                        #   select(each, add=True)
                        #   if(fullname_list.count(each)>1):
                        #       print 'more'
                        print fullname_list
                        cmds.select(fullname_list)
                        #print 'all the items: ' + str(fullname_list)
                        #cmds.select('PR_char_kamila_v007:spine_4_anim')
                        #print 'after blah'
                        #print 'picked '+the_who+':', pick_list
                    if len(skip_list)>0:
                        pass
                        #print 'skipped '+the_who+':', skip_list
                except:
                    cmds.select(clear=True)
                    #print 'who: ' + the_who
                    #raise Exception('Error selecting those objects', pick_list)
                    print 'Error selecting those objects', pick_list
            else:
                print 'nothing to do'
        return do_select_sub

    def move_button(self, one_button):
        print 'moving'
        line_number = one_button['line_num']

        print self._all_lines[line_number]

    def redirect(self,theCommand, what):
        def redirect_sub(*args):
            # "*args" is still required because this is the
            # function that Maya will ultimately call when
            # the button is pushed

            if theCommand == 'IKSwitch':
                IKSwitch(self._who, 'hand')
            elif theCommand =='write out':
                write_buttons()
            elif theCommand =='selectAll':
                select_all_items(self._who)
            elif theCommand =='switchAttrib':
                self.switch_attribute(what)
            elif theCommand == 'move':
                self.move_button(what)
            elif theCommand == 'setAttrib':
                self.set_attribute(what)
            elif theCommand == 'addAttrib':
                self.tweak_attributes(what)
            elif theCommand == 'subAttrib':
                self.tweak_attributes(what, negative=True)
            elif theCommand == 'adjustAttrib':
                self.adjust_attributes(what)
            elif theCommand == 'refresh':
                self.launch_window()
            else:
                print 'undefined command :', theCommand
        return redirect_sub

    def load_buttons(self):
        '''
        General load function to get into the file and pull parse the data
        Returns a list of dictionaries of buttons with the format:
            {'label', 'top', 'left', 'height', 'width', 'bgcol', 'command', 'items'}
        update 27 Feb - also gets the window properties from the file
        update 31 Jan - also pulls the tabs from the file
        '''

        #initialise the list
        current_tab = ''
        current_buttonlist = []
        current_controlsList = []
        #self._tabs_list.append(Tab(title='no title', bgimage='nothing.bmp'))
        all_controls = []
        #cur_tab = 0
        #file_name = fileDialog2(fileFilter=singleFilter, dialogStyle=2, okCaption='Open')
        file_name = self._pwd+self._buttons_file
        with open(file_name, 'r') as openfile:
            self._all_lines = openfile.readlines()
        openfile.close()
        for position, each_item in enumerate(self._all_lines):
            #try:
                #if each_item[0] != '#':
                    # window
                    if len(each_item) < 1:
                        print 'too small'
                        break
                    if each_item[0] == 'w':
                        window_properties = each_item.split(':')
                        self._window_title = window_properties[1]
                        self._window_width = int(window_properties[3])
                        self._window_height = int(window_properties[5])

                    # label / extra
                    elif each_item[0] in ['l','e'] :
                        #get all the properties
                        props = each_item.split(':')
                        #parse the floats for the colour
                        the_floats = props[11][1:-1].split(',')
                        #make the thing that'll get passed into the button dictionary
                        command = props[13][:]

                        #chop off the end of line char and get rid of spaces in the names
                        the_item_string = props[15][:-2].replace(" ","")
                        the_items = the_item_string.split(',')

                        itemDict = {props[0][:]:props[1][:],   # label
                                    props[2][:]:int(props[3]), # top
                                    props[4][:]:int(props[5]), # left
                                    props[6][:]:int(props[7]), # height
                                    props[8][:]:int(props[9]), # width
                                    props[10][:]:[float(the_floats[0]),float(the_floats[1]),float(the_floats[2])], # bgcol
                                    props[12][:]:command,      # command
                                    props[14][:]:the_items,
                                    'line_num':position}    # items

                        a_button = Button(label=props[1][:],
                                          top=int(props[3]),
                                          left=int(props[5]),
                                          height=int(props[7]),
                                          width=int(props[9]),
                                          bgcol=[float(the_floats[0]),float(the_floats[1]),float(the_floats[2])], # bgcol
                                          command=command,     # command
                                          items=the_items)

                        self._all_buttons.append(a_button)

                        try:
                            self._tabs_list[-1].add_button(a_button)
                        except:
                            pass

                        if each_item[0] == 'l':
                            current_buttonlist.append(itemDict)
                        else:
                            self._extra_buttons.append(itemDict)

                    # control
                    elif each_item[0] == 'c':
                        pass
                    # tab
                    elif each_item[0] == 't':
                        props = each_item.split(':')
                        #   a_tab = Tab(label=props[1][:], bgimage=props[3][:-2])
                        #   self._tabs_list.append(a_tab)
                        #   print 'making a tab %s' % (props[1][:])
                        tab_name = str(props[1][:])
                        #if there arent any tabs yet, make one and start
                        # a_new_tab = Tab(label='this is a label', bgimage='image.png')
                        # self._tabs_list.append(a_new_tab)
                        #add the current tab to the tabs list
                        #current_tab_obj = Tab(title='no title', bgimage='nothing.bmp')
                        self._tabs_list.append(Tab(title=tab_name, bgimage='nothing.bmp'))
                        if self.num_tabs() == 0:
                            print 'number of tabs is 0'
                        if not current_tab:
                            #print 'here'
                            props = each_item.split(':')
                        #   a_tab = Tab(label=props[1][:], bgimage=props[3][:-2])
                        #   self._tabs_list.append(a_tab)
                        #   print 'making a tab %s' % (props[1][:])
                            current_tab = props[1][:]
                            tab_bgimage = props[3][:-2] # -2 strips off the EOL
                        else:
                            #print 'also here'
                            all_controls.append([current_tab, tab_bgimage, current_buttonlist[:], current_controlsList[:]])
                            current_buttonlist = []
                            current_controlsList = []
                            props = each_item.split(':')
                            current_tab = props[1][:]
                            tab_bgimage = props[3][:-2] # -2 strips off the EOL
                    elif each_item[0] =='#':
                        pass
                        #print 'comment'
                    else:
                        pass
                        #print 'nothing'
                #else:
                    #print 'empty line'
            #except:
                #empty line
                #print 'empty line or error'
                #pass
                    #print position
        # done so add the last one to the list
        all_controls.append([current_tab, tab_bgimage, current_buttonlist[:]])

        return all_controls

    def load_xml_buttons(self):
        '''
        Loads all the button positions and other settings from the XML rather than the TEXT file
        '''
        print 'loading XML'

    def prettify(self, elem):
        """Return a pretty-printed XML string for the Element.
        """
        from xml.dom import minidom
        try:
            rough_string = ET.tostring(elem, 'utf-8')
        except Exception, e:
            raise e
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="\t")

    def write_xml_buttons(self):
        '''
        write the same thing but this time in XML format somehow
        '''
        alltabs = []
        window_element = ET.Element('window',
                                     width=str(self._window_width),
                                     height=str(self._window_height),
                                     title=self._window_title)
        for tab in self._tabs_list:
            tab_element = ET.SubElement(window_element,
                                        tag='tab',
                                        title=tab.get_title())
            for button in tab.all_buttons():
                button_element = ET.SubElement(tab_element,
                                  tag='button',
                                  label=button.get_name(),
                                  left=str(button.get_left()),
                                  top=str(button.get_top()),
                                  height=str(button.get_height()),
                                  width=str(button.get_width()),
                                  bgcol=button.get_bgcol_str(),
                                  command=str(button.get_command()))
                if button.get_command() == 'select':
                    all_items = ''
                    for item in button.get_items():
                        all_items += str(item) + '\n\t\t\t\t'
                    item_element = ET.SubElement(button_element, tag='items')
                    item_element.text = all_items[:-5] # -5 to strip the new line and last set of tabs
                else:
                    for item in button.get_items():
                        min_max = button.get_min_max(item)
                        clean_item = button.get_item_only(item)
                        #we still want to put in the min and max for relevant items
                        if min_max:
                            item_element = ET.SubElement(button_element,
                                                         tag='item',

                                                         min=min_max[0],
                                                         max=min_max[1])
                            item_element.text = clean_item
                        else:
                            item_element = ET.SubElement(button_element,
                                                         tag='item',
                                                         value='coming_soon')
                            item_element.text = clean_item
        tree = ET.ElementTree(window_element)
        tree.write(self._pwd+'/output.xml')
        file_name = self._pwd+'/outputnice.xml'
        with open(file_name, 'w') as openfile:
            openfile.write(self.prettify(window_element))
        openfile.close()

    def connect_face(self):
        '''
        This runs through the sliders and the controls and connects them
        It's dynamic to allow for the change of 'who'
        '''
        for to_connect in self._face_sliders:
            to_con_attribs = []
            for one_who in self._who:
                # BOOM!
                for one_attr in to_connect[1]:
                    to_con_attribs.append(one_who+':'+one_attr)
            cmds.connectControl(to_connect[0], to_con_attribs)

    def set_tweak(self,number):
        def st_sub(*args):
            self._tweak = float(number)/100
            print self._tweak
        return st_sub

    def make_slider(self, left, top, parent_form):
        '''
        This just makes the physical slider - it connects nothing. That's done dynamically
        '''
        the_field = cmds.floatSlider(width=80, min=0, max=1, value=0, step=0.05 )
        cmds.formLayout(parent_form,
                        edit=True,
                        attachForm=[(the_field, 'top', top),
                                    (the_field, 'left', left)])
        return the_field

    def make_button_group(self, left, top, parent_form):
        '''
        Sub routine for making the buttons in groups

        '''
        pass
        # heres what we get given
        # label:Oh:top:281:left:5:height:15:width:50:bgcol:[0.8,0.8,0.8]:command:select:items:
        # label:-:top:281:left:154:height:15:width:23:bgcol:[0.6,0.6,0.6]:command:subAttrib:items:Mouth_Blend_Ctrl.Phoneme_Oh+0.2
        # label:0:top:281:left:178:height:15:width:23:bgcol:[0.8,0.8,0.8]:command:setAttrib:items:Mouth_Blend_Ctrl.Phoneme_Oh=0.0
        # label:Oh:top:281:left:202:height:15:width:23:bgcol:[0.8,0.8,0.8]:command:setAttrib:items:Mouth_Blend_Ctrl.Phoneme_Oh=1.0
        # label:+:top:281:left:226:height:15:width:23:bgcol:[0.6,0.6,0.6]:command:addAttrib:items:Mouth_Blend_Ctrl.Phoneme_Oh+0.2

    def launch_window(self):
        '''
        Just show the window - there is an assumption that there is already a list loaded
        make a window
        make a form
        set the label and size of each button
        '''
        icon_image = self._pwd+self._pwd_img+'iconTest.png'

        # set default who (just the first one)
        self._who.append(self._the_who_list[0])

        #check to see if the UI exists
        if cmds.window("meltGui", exists=True):
            cmds.deleteUI("meltGui")

        #create the window and main form
        window = cmds.window("meltGui",
                              title=self._window_title,
                              w=self._window_width,
                              h=self._window_height,
                              mnb=False,
                              mxb=False,
                              sizeable=False)
        form_main = cmds.formLayout(numberOfDivisions=100)

        # _________________________________________
        #
        #  TABS
        # _________________________________________

        tabs = cmds.tabLayout(innerMarginWidth=5,
                              innerMarginHeight=5,
                              height=(self._window_height-self._WHO_HEIGHT-self._EXTRA_HEIGHT))
        cmds.formLayout(form_main,
                        edit=True,
                        attachForm=((tabs, 'top', 0), (tabs, 'left', 0)))
        # the controls list is a list of tabs, each with a set of buttons
        for tab in self._controls_list:
            current_tab = cmds.formLayout(numberOfDivisions=100)
            # Get the backdrop image if there is one
            backdrop_file = self._pwd+'/'+tab[1]
            cmds.image('bgImage',
                        width=self._window_width,
                        height=self._window_height,
                        parent=current_tab,
                        image=backdrop_file)

            #get the list of buttons for this tab
            button_list = tab[2][:]

            for buttn in button_list:
                if not self._debug:
                    if buttn['command'] == 'select':
                        #standard selection button
                        new_button = cmds.button(label=buttn['label'],
                                                 height=buttn['height'],
                                                 width=buttn['width'],
                                                 backgroundColor=buttn['bgcol'],
                                                 command=self.do_select(buttn['items'][:]))
                    else:
                        #for buttons with other functions
                        new_button = cmds.button(label=buttn['label'],
                                                 height=buttn['height'],
                                                 width=buttn['width'],
                                                 backgroundColor=buttn['bgcol'],
                                                 command=self.redirect(buttn['command'][:], buttn['items'][:]))
                else:
                    #for placing the buttons carefully
                    print buttn['label']+'_'+str(buttn['top'])+'_'+str(buttn['left'])
                    new_button = cmds.button(label=buttn['label'],
                                             height=buttn['height'],
                                             width=buttn['width'],
                                             backgroundColor=buttn['bgcol'],
                                             command=self.redirect('move', buttn, ))
                #attach the button to the form
                cmds.formLayout(current_tab,
                                edit=True,
                                attachForm=[(new_button, 'top', buttn['top']), (new_button, 'left', buttn['left'])])
            tweak_left = 10
            tweak_top = 410
            cur_top = 42
            lft_left = 255
            mid_left = 160
            rgt_left = 65
            tweaks = ['10','20','30','40','50','60','70','80','90','100']
            tweak_width=25
            if (tab[0] == 'Mouth') or (tab[0]=='MouthTidy'):
                # the_tweak_label = cmds.text( label='Tweak' )
                # the_tweak = cmds.floatSliderGrp(cw2=[50,70], min=0, max=1, field=True, value=0.1, step=0.05, changeCommand=lambda x:self.set_tweak(x))
                # cmds.formLayout(current_tab,
                #               edit=True,
                #               attachForm=[(the_tweak, 'top', tweak_top), (the_tweak, 'left', tweak_left+40),
                #                           (the_tweak_label, 'top',tweak_top+5), (the_tweak_label, 'left', tweak_left)])
                mouth_tweak_label = cmds.text( label='Tweak' )
                cmds.formLayout(current_tab,
                                edit=True,
                                attachForm=[(mouth_tweak_label, 'top',tweak_top+5),
                                            (mouth_tweak_label, 'left', tweak_left)])

                tweak_buttons_left = tweak_left+40

                for i,tweak_one in enumerate(tweaks):
                    tweak_but = cmds.button(label=tweak_one, width=tweak_width-2, command=self.set_tweak(tweak_one[:]))
                    cmds.formLayout(current_tab,
                                    edit=True,
                                    attachForm=[(tweak_but, 'top', tweak_top),
                                                (tweak_but, 'left', tweak_buttons_left)])
                    tweak_buttons_left += tweak_width
                for attrib in self._mouth_attribs:
                    if attrib[-1:] == 'L':
                        new_L_slider = self.make_slider(left=lft_left, top=cur_top, parent_form=current_tab)
                        self._face_sliders.append([new_L_slider,[attrib]])
                        new_R_slider = self.make_slider(left=rgt_left, top=cur_top, parent_form=current_tab)
                        self._face_sliders.append([new_R_slider,[attrib[:-1]+'R']])
                        new_M_slider = self.make_slider(left=mid_left, top=cur_top, parent_form=current_tab)
                        self._face_sliders.append([new_M_slider,[attrib,attrib[:-1]+'R']])
                        cur_top += 32
                    elif (attrib[-4:] == 'Pull'):
                        new_M_slider = self.make_slider(left=mid_left, top=cur_top, parent_form=current_tab)
                        self._face_sliders.append([new_M_slider,[attrib]])
                        cur_top += 32
                    elif (attrib[-2:] == 'FV') or (attrib[-6:] == 'Toothy'):
                        new_M_slider = self.make_slider(left=rgt_left, top=cur_top, parent_form=current_tab)
                        self._face_sliders.append([new_M_slider,[attrib]])
                    elif attrib[-2:-1] == 'O':
                        new_M_slider = self.make_slider(left=mid_left, top=cur_top, parent_form=current_tab)
                        self._face_sliders.append([new_M_slider,[attrib]])
                    elif attrib[-3:] == 'BMP':
                        new_M_slider = self.make_slider(left=lft_left, top=cur_top, parent_form=current_tab)
                        self._face_sliders.append([new_M_slider,[attrib]])
                        cur_top += 32

                self.make_button_group(left=lft_left, top=cur_top+40, parent_form=current_tab)


            elif tab[0] == 'Brow':
                brow_tweak_label = cmds.text( label='Tweak' )
                cmds.formLayout(current_tab,
                                edit=True,
                                attachForm=[(brow_tweak_label, 'top',tweak_top+5),
                                            (brow_tweak_label, 'left', tweak_left)])
                tweak_buttons_left = tweak_left+40
                for tweak_one in tweaks:
                    tweak_but = cmds.button(label=tweak_one, width=tweak_width-2)
                    cmds.formLayout(current_tab,
                                    edit=True,
                                    attachForm=[(tweak_but, 'top', tweak_top),
                                                (tweak_but, 'left', tweak_buttons_left)])
                    tweak_buttons_left += tweak_width

                cur_top = 61
                for attrib in self._brow_attribs:
                    brow_L_slider = self.make_slider(left=lft_left, top=cur_top, parent_form=current_tab)
                    self._face_sliders.append([brow_L_slider,[attrib+'L']])
                    brow_M_slider = self.make_slider(left=mid_left, top=cur_top, parent_form=current_tab)
                    self._face_sliders.append([brow_M_slider,[attrib+'L',attrib+'R']])
                    brow_R_slider = self.make_slider(left=rgt_left, top=cur_top, parent_form=current_tab)
                    self._face_sliders.append([brow_R_slider,[attrib+'R']])
                    cur_top += 42

            cmds.setParent('..')
            cmds.tabLayout(tabs,
                           edit=True,
                           tabLabel=((current_tab, tab[0])))
        cmds.setParent('..')

        # _________________________________________
        #
        #  EXTRAS
        # _________________________________________
        #extras_frame = cmds.frameLayout(label='Extras', collapsable=True)
        #cmds.formLayout(form_main,
                        # edit=True,
                        # attachForm=[(extras_frame, 'top', self._window_height-(self._WHO_HEIGHT+self._EXTRA_HEIGHT)),
                        #           (extras_frame, 'left', 0)])
        extras_form = cmds.formLayout(numberOfDivisions=100, height=self._EXTRA_HEIGHT)
        cmds.formLayout(form_main,
                        edit=True,
                        attachForm=[(extras_form, 'top', self._window_height-(self._WHO_HEIGHT+self._EXTRA_HEIGHT)),
                                    (extras_form, 'left', 0)])

        extras_buttons_pos = {'left':10, 'top':10}

        for extra in self._extra_buttons:
            extra_button = cmds.button(label=extra['extra'],
                                       height=extra['height'],
                                       width=extra['width'],
                                       backgroundColor=extra['bgcol'],
                                       command=self.redirect(extra['command'][:], extra['items'][:]))
            cmds.formLayout(extras_form,
                            edit=True,
                            attachForm=[(extra_button, 'top',  extras_buttons_pos['top']),
                                        (extra_button, 'left', extras_buttons_pos['left'])])
            extras_buttons_pos['left'] += (extra['width'] + 2)

            #wrap to the next line
            if extras_buttons_pos['left'] + extra['width'] > self._window_width:
                extras_buttons_pos['left'] = 10
                extras_buttons_pos['top'] += (extra['height'] + 2)

        cmds.setParent('..')
        cmds.setParent('..')

        # _________________________________________
        #
        #  WHO
        # _________________________________________

        who_form = cmds.formLayout(numberOfDivisions=100, height=self._WHO_HEIGHT)
        cmds.formLayout(form_main,
                        edit=True,
                        attachForm=((who_form, 'top', self._window_height-self._WHO_HEIGHT),
                                    (who_form, 'left', 0)))
        # initial position for the who-buttons
        who_buttons_pos = {'left':10, 'top':10}
        # if we managed to load some characters
        if(self._the_who_list[0]!='_none'):
            print('the who list:', self._the_who_list)
            for eachWho in self._the_who_list:
                # Just pull out the name of the character
                newname = eachWho.split('_')[1]
                # make a button id based on the tab and the item to set who
                who_button = cmds.button(eachWho,
                                         label=newname,
                                         height=20,
                                         width=70,
                                         command=self.set_who(eachWho))
                # slap it onto the form
                cmds.formLayout( who_form,
                                 edit=True,
                                 attachForm=[(who_button, 'top',  who_buttons_pos['top']),
                                             (who_button, 'left', who_buttons_pos['left'])])
                who_buttons_pos['left'] += 72
                # put it into a list so we can change its colour later
                self._who_buttons.append(who_button)
            #just colouring the button to indicate the first one is selected
            cmds.button(self._the_who_list[0], edit=True, backgroundColor=self._WHO_BUTTON_COLOUR_SELECTED)
        else:
            # make a button that indicates there is nothing loaded
            none_button = cmds.button(label='No Characters Found',
                                      height=20,
                                      width=120)
            # slap it onto the form
            cmds.formLayout( who_form,
                             edit=True,
                             attachForm=[(none_button, 'top',  who_buttons_pos['top']),
                                         (none_button, 'left', who_buttons_pos['left'])])
            self._who = ['none']
            print 'no who'
        self.connect_face()
        # **** THIS IS AN ICON BUTTON TEST THING -----
        #testButton = cmds.iconTextButton( style='iconOnly', image1=icon_image, label='testButton', command=do_select(['Head_Ctrl'], whoOptionMenu))
        #cmds.formLayout( formTab1, edit=True, attachForm=[(testButton, 'top', 300), (testButton, 'left', 200)])
        #show the window
        cmds.showWindow(window)
        #self.write_buttons()

    def switch_attribute(self, what):
        '''
        switch the attribute
        NEEDS IMPROVEMENT - not at all class based - just reuse of the previous version of it
        '''
        for one_who in self._who:
            # temporary fault check thing - take out ASAP
            if one_who == 'none':
                who = ''
            else:
                who = one_who + ':'

            for attrib in what:
                #check to see if it exists
                newValue = 1 - cmds.getAttr(who+attrib)
                cmds.setAttr(who+attrib, newValue)

    def set_attribute(self, what):
        '''
        set various attributes for various items - first we need to split it up
        '''

        for one_who in self._who:
            # temporary fault check thing - take out ASAP
            if one_who == 'none':
                who = ''
            else:
                who = one_who + ':'
            for each_pair in what:
                extracted = each_pair.split('=')
                the_attrib = extracted[0]
                the_value = extracted[1]
                if 'CONTROL' in self.modifier_pressed():
                    print ' here'
                    self.tweak_attributes([the_attrib+'+0.1'])
                else:
                    cmds.setAttr(who+the_attrib, float(the_value))

    def adjust_attributes(self, what):
        '''
        set various attributes for various items - first we need to split it up
        '''

        for one_who in self._who:
            # temporary fault check thing - take out ASAP
            if one_who == 'none':
                who = ''
            else:
                who = one_who + ':'
            for each_pair in what:
                extracted = each_pair.split('[')
                the_attrib = extracted[0]
                the_values = extracted[1][:-1].split('|')   # chop off the  at the end and split by |
                min_max_val = the_values[0]
                incr_val = the_values[1]
                if 'CONTROL' in self.modifier_pressed():
                    new_value = float(min_max_val)
                else:
                    current_value = cmds.getAttr(who+the_attrib)
                    new_value = current_value + float(incr_val)
                cmds.setAttr(who+the_attrib, new_value)

    def tweak_attributes(self, what, amount=0.1, negative=False):
        '''
        add the tweak to each of the attributes in the list
        setting negative to True tweaks DOWN
        '''

        map
        # add the tweak as a SCALE factor
        for one_who in self._who:
            # temporary fault check thing - take out ASAP
            if one_who == 'none':
                who = ''
            else:
                who = one_who + ':'
            for each_pair in what:
                the_attrib = who + each_pair.split('+')[0]
                current_value = cmds.getAttr(the_attrib)
                if negative:
                    new_value = current_value - self._tweak
                else:
                    new_value = current_value + self._tweak
                cmds.setAttr(the_attrib, new_value)

    def select_all_items(who):
        '''
        We need logic to check for names that aren't part of a given rig
        '''
        print 'selecting all the stuff'

#new_picker = Picker()
#new_picker.launch_window()
# new_picker.write_xml_buttons()