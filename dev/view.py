from enum import Enum

from logger import log


class ViewMode(Enum):
    TEXT = 'text'
    GRAPHICAL = 'graphical'


class View:
    def __init__(self, mode):
        assert mode in ViewMode, "Mode must be an instance of ViewMode Enum"
        self.mode = mode

    def update(self, data):
        if self.mode == ViewMode.TEXT:
            self._update_text(data)
        elif self.mode == ViewMode.GRAPHICAL:
            self._update_graphical(data)

    def _update_text(self, data):
        log(f"Text View Updated with data: {data}")
        # TODO: Implement text update logic

    def _update_graphical(self, data):
        raise NotImplementedError("Graphical view is not implemented yet")

    def render(self):
        if self.mode == ViewMode.TEXT:
            self._render_text()
        elif self.mode == ViewMode.GRAPHICAL:
            self._render_graphical()

    def _render_text(self):
        log('(NOT IMPLEMENTED) Rendering Text View')
        # TODO: Implement text rendering logic
        # think about using C to accelerate rendering

    def _render_graphical(self):
        raise NotImplementedError("Graphical rendering is not implemented yet")
    
