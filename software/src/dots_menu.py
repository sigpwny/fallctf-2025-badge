from badgeio import display
from menu import Menu, menu_controller


class DotsMenu(Menu):
    def on_focus(self):
        display.fill(0)

    def draw(self):
        i = (menu_controller.cur_tick // 500) % 6
        if i == 0:
            display.fillcircle((64, 100), 5, display.WHITE)
        elif i == 1:
            display.fillcircle((64, 80), 5, display.WHITE)
        elif i == 2:
            display.fillcircle((64, 60), 5, display.WHITE)
        elif i == 3:
            display.fillcircle((64, 100), 5, display.BLACK)
        elif i == 4:
            display.fillcircle((64, 80), 5, display.BLACK)
        elif i == 5:
            display.fillcircle((64, 60), 5, display.BLACK)
