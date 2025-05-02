from badgeio import display, joystick, a_btn, b_btn, tick_buttons
import time
from sysfont import sysfont


class MenuController:
    """
    Controller logic for managing the menu stack.
    The top menu will be drawn and receive button presses.
    """

    def __init__(self):
        self.menu_stack: list[Menu] = []
        self.cur_tick = 0
        self.last_tick = 0
        self.delta_tick = 0
        """Time (in ms) between the last tick and the current one. Useful for timing animations."""

    def push_menu(self, menu: "Menu"):
        """
        Add a menu to the menu stack.
        """
        if len(self.menu_stack) > 0:
            self.menu_stack[-1].on_unfocus()
        self.menu_stack.append(menu)
        menu.on_enter()
        menu.on_focus()

    def pop_menu(self):
        """
        Remove a menu from the menu stack.
        """
        # Bottommost menu should be main menu, so don't pop that
        if len(self.menu_stack) > 1:
            self.menu_stack[-1].on_unfocus()
            self.menu_stack[-1].on_leave()
            self.menu_stack.pop()
            self.menu_stack[-1].on_focus()

    def pop_to_bottom(self):
        """
        Pops all byt the bottommost menu.
        This is useful e.g. if you have nested options menus and want to return to the main menu quickly.
        """
        while len(self.menu_stack) > 1:
            self.pop_menu()

    def swap_menu(self, menu: "Menu"):
        """
        Swaps the topmost menu with a new one.
        """
        self.pop_menu()
        self.push_menu(menu)

    def run_loop(self):
        """
        Run the main control loop.
        This includes handling inputs, menu updating, and rendering.
        """
        while True:
            tick_buttons()

            if a_btn.pressed:
                self.menu_stack[-1].a_pressed()

            if b_btn.pressed:
                self.menu_stack[-1].b_pressed()

            self.last_tick = self.cur_tick
            self.cur_tick = time.ticks_ms()
            self.delta_tick = time.ticks_diff(self.cur_tick, self.last_tick)

            # Tick the current menu
            self.menu_stack[-1].tick()
            self.menu_stack[-1].draw()

            # Update the display
            # display.show()


class Menu:
    """
    Base class for all Menus
    """

    def tick(self):
        """
        Called every tick before draw().
        Handles logic for the menu such as checking inputs and updating internal state.
        """
        pass

    def draw(self):
        """
        Called every tick after update().
        Handles displaying the menu.
        """
        display.fill(0)

    def a_pressed(self):
        pass

    def b_pressed(self):
        """
        This default implementation will return to the previous menu
        """
        global menu_controller
        menu_controller.pop_menu()

    def on_enter(self):
        """
        Called whenever a menu is initially pushed onto the stack
        """
        pass

    def on_leave(self):
        """
        Called whenever a menu leaves the stack
        """
        pass

    def on_focus(self):
        """
        Called whenever a menu becomes active (i.e. when it gets pushed onto the stack, and when the menu on top of it gets popped)
        """
        pass

    def on_unfocus(self):
        """
        Called whenever a menu becomes no longer active (see on_focus())
        """
        pass


class RowMenu(Menu):
    """
    A basic menu that displays a list of items, one per row
    """
    class RowItem:
        def __init__(self, label: str, action):
            self.label = label
            self.action = action

    def __init__(self, items: list[RowItem]):
        self.items = items
        self.selected_idx = 0
        self.ticks_since_move = 0

    def on_focus(self):
        # need to clear the screen since draw() doesn't use the whole screen
        display.fill(0)

    def tick(self):
        global menu_controller
        self.ticks_since_move += menu_controller.delta_tick
        if joystick.y != 0 and self.ticks_since_move >= 500:
            self.ticks_since_move = 0
            self.selected_idx = (
                self.selected_idx + (1 if joystick.y() else -1)) % len(self.items)

    def draw(self):
        # display.fill(0) causes a lot of flickering

        num_cols = display.size()[0] // sysfont["Width"]
        num_rows = display.size()[1] // sysfont["Height"]
        start_i = max(0, self.selected_idx -
                      num_rows // 2)  # allow scrolling
        y = 0
        for i in range(start_i, min(num_rows + start_i, len(self.items))):
            if i == self.selected_idx:
                display.text(
                    (0, y), f"> {self.items[i].label}", display.WHITE, sysfont)
            else:
                display.text(
                    (0, y), f"  {self.items[i].label}", display.WHITE, sysfont)
            y += sysfont["Height"]
        display.text(
            (0, y), " " * num_cols, display.WHITE, sysfont)

    def a_pressed(self):
        if self.selected_idx >= len(self.items):
            print("Out of bounds")
            return

        self.items[self.selected_idx].action()


menu_controller = MenuController()
