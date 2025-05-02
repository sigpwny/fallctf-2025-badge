from menu import menu_controller, Menu, RowMenu


test_menu_0 = Menu()
test_menu_1 = RowMenu([
    RowMenu.RowItem("q", lambda: print("q")),
    RowMenu.RowItem("w", lambda: print("w")),
    RowMenu.RowItem("e", lambda: print("e")),
    RowMenu.RowItem("r", lambda: print("r")),
    RowMenu.RowItem("t", lambda: print("t")),
    RowMenu.RowItem("y", lambda: print("y")),
    RowMenu.RowItem("u", lambda: print("u")),
    RowMenu.RowItem("i", lambda: print("i")),
    RowMenu.RowItem("o", lambda: print("o")),
    RowMenu.RowItem("p", lambda: print("p")),
    RowMenu.RowItem("a", lambda: print("a")),
    RowMenu.RowItem("s", lambda: print("s")),
    RowMenu.RowItem("d", lambda: print("d")),
])
test_menu_2 = RowMenu([
    RowMenu.RowItem("blank", lambda: menu_controller.push_menu(test_menu_0)),
    RowMenu.RowItem("letters", lambda: menu_controller.push_menu(test_menu_1)),
])
menu_controller.push_menu(test_menu_2)

menu_controller.run_loop()
