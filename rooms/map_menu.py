import logging
import traceback

import room
import rooms
import gui
import resources
import colors as c
import fonts as f
import state as s


class MapMenu(gui.Container):
    def __init__(self, image):
        super().__init__(layout_gravity=gui.Gravity.FILL, gravity=gui.Gravity.CENTER, bg_color=c.BLACK, bg_image=image)
        self.files = [(f, self.chosen) for f in resources.list_maps()]
        self.choose_label = gui.Label(_("Choose a map!"), f.MAIN_MENU, txt_color=c.ICE, bg_color=c.MENU_BG)
        self.menu = gui.Menu(self.files, f.MAIN, padding=(25, 25), die_when_done=False)
        self.back_btn = gui.Button(_("Go Back"), f.MAIN, callback=self.back, layout_gravity=gui.Gravity.BOTTOMRIGHT)
        self.add_children(self.choose_label, self.menu, self.back_btn)

    def back(self, *_):
        self.done = True
        self.next = rooms.MainMenu()

    def chosen(self, menu, choice):
        map_path = resources.map_path(choice)
        try:
            s.load_map(map_path)
        except:
            msg = _("Error while loading map \"%s\"! Please report this issue.\n\n%s") % (map_path, traceback.format_exc())
            logging.error(msg)
            dialog = gui.Dialog(msg, f.MONOSPACE, layout_gravity=gui.Gravity.FILL, padding=25)
            room.run_room(dialog)
        else:
            self.done = True
