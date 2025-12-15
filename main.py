#!/usr/bin/env python3

from textual.app import App
from textual.binding import Binding

from src.menu import MenuScreen
from src.space import SpaceScenario
from src.military import MilitaryScenario


class DTNSimulationApp(App):
    """Main DTN Simulation Application."""
    
    TITLE = "DTN Simulation"
    SUB_TITLE = "Delay Tolerant Network Simulator"
    
    CSS = """
    Screen {
        background: $surface;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("ctrl+q", "quit", "Quit", show=False),
    ]
    
    SCREENS = {
        "menu": MenuScreen,
        "space": SpaceScenario,
        "military": MilitaryScenario,
    }
    
    def on_mount(self) -> None:
        self.push_screen("menu")


def main():
    app = DTNSimulationApp()
    app.run()


if __name__ == "__main__":
    main()