from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button
from textual.containers import Center, Vertical


LOGO = """
██████╗ ████████╗███╗   ██╗
██╔══██╗╚══██╔══╝████╗  ██║
██║  ██║   ██║   ██╔██╗ ██║
██║  ██║   ██║   ██║╚██╗██║
██████╔╝   ██║   ██║ ╚████║
╚═════╝    ╚═╝   ╚═╝  ╚═══╝

Delay Tolerant Network Simulation
"""


class MenuScreen(Screen):
    """Main menu screen for scenario selection."""
    
    CSS = """
    MenuScreen {
        align: center middle;
        background: $surface;
    }
    
    #main-container {
        width: auto;
        height: auto;
        align: center middle;
    }
    
    #logo {
        width: auto;
        text-align: center;
        color: white;
        margin-bottom: 3;
    }
    
    #button-group {
        width: 30;
        height: auto;
    }
    
    Button {
        width: 100%;
        height: auto;
        margin: 1 0;
        border: none;
        background: transparent; 
        content-align: left middle;
    }
    
    Button:focus {
        text-style: bold;
        background: transparent;
    }
    
    Button:hover {
        text-style: underline;
        background: transparent;
    }
    
    #space-btn {
        color: #00bfff;
    }
    
    #military-btn {
        color: #32cd32;
    }
    
    #quit-btn {
        color: #ff4500;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="main-container"):
                yield Static(LOGO, id="logo")
                
                with Vertical(id="button-group"):
                    yield Button("Space Scenario", id="space-btn")
                    yield Button("Military Scenario", id="military-btn")
                    yield Button("Quit", id="quit-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        
        if button_id == "space-btn":
            self.app.push_screen("space")
        elif button_id == "military-btn":
            self.app.push_screen("military")
        elif button_id == "quit-btn":
            self.app.exit()
