"""Space scenario for DTN simulation - Mars to Earth communication with orbital animation."""

import asyncio
import math
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Button, Footer, Header
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual import work
from rich.text import Text
from rich.panel import Panel
from rich.table import Table

from src.dtn_core import Node, Packet, PacketType, Buffer


class OrbitalView(Static):
    """A 2D canvas showing celestial bodies with orbiting satellites."""
    
    orbit_phase: reactive[float] = reactive(0.0)
    transmitting_link: reactive[int] = reactive(-1)
    transmit_progress: reactive[float] = reactive(0.0)
    
    link0_visible: reactive[bool] = reactive(True)
    link1_visible: reactive[bool] = reactive(False)
    link2_visible: reactive[bool] = reactive(False)
    link3_visible: reactive[bool] = reactive(False)
    link4_visible: reactive[bool] = reactive(False)
    link5_visible: reactive[bool] = reactive(True)
    
    mars_sat_buffer: reactive[int] = reactive(0)
    moon_sat1_buffer: reactive[int] = reactive(0)
    moon_sat2_buffer: reactive[int] = reactive(0)
    earth_sat_buffer: reactive[int] = reactive(0)
    
    moon_sat1_is_blackhole: reactive[bool] = reactive(False)
    earth_antenna_off: reactive[bool] = reactive(False)
    
    _sat_positions: list[tuple[int, int]] = []
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.width = 100
        self.height = 20
    
    def render(self) -> Text:
        canvas = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        # Center the three planets evenly across the canvas
        center_y = self.height // 2
        margin = 15  # Margin from edges
        usable_width = self.width - 2 * margin
        spacing = usable_width // 2
        
        mars_pos = (margin + 0, center_y)
        moon_pos = (margin + spacing, center_y)
        earth_pos = (margin + 2 * spacing, center_y)
        
        self._draw_planet(canvas, mars_pos[0], mars_pos[1], "MARS", "M", 3, 5)
        self._draw_planet(canvas, moon_pos[0], moon_pos[1], "MOON", "L", 2, 4)
        self._draw_planet(canvas, earth_pos[0], earth_pos[1], "EARTH", "E", 3, 5)
        
        mars_sat_angle = self.orbit_phase * 1.5
        mars_sat_x = int(mars_pos[0] + 10 * math.cos(mars_sat_angle))
        mars_sat_y = int(mars_pos[1] + 5 * math.sin(mars_sat_angle))
        
        moon_sat1_angle = self.orbit_phase * 2.0
        moon_sat1_x = int(moon_pos[0] + 8 * math.cos(moon_sat1_angle))
        moon_sat1_y = int(moon_pos[1] + 4 * math.sin(moon_sat1_angle))
        
        moon_sat2_angle = self.orbit_phase * 2.0 + math.pi
        moon_sat2_x = int(moon_pos[0] + 8 * math.cos(moon_sat2_angle))
        moon_sat2_y = int(moon_pos[1] + 4 * math.sin(moon_sat2_angle))
        
        # Earth satellite - orbits Earth
        earth_sat_angle = self.orbit_phase * 1.8 + 0.5
        earth_sat_x = int(earth_pos[0] + 10 * math.cos(earth_sat_angle))
        earth_sat_y = int(earth_pos[1] + 5 * math.sin(earth_sat_angle))
        
        # Draw orbit paths (dotted circles)
        self._draw_orbit_path(canvas, mars_pos[0], mars_pos[1], 10, 5)
        self._draw_orbit_path(canvas, moon_pos[0], moon_pos[1], 8, 4)
        self._draw_orbit_path(canvas, earth_pos[0], earth_pos[1], 10, 5)
        
        self._draw_satellite(canvas, mars_sat_x, mars_sat_y, "M-S", self.mars_sat_buffer, False)
        self._draw_satellite(canvas, moon_sat1_x, moon_sat1_y, "L1", self.moon_sat1_buffer, self.moon_sat1_is_blackhole)
        self._draw_satellite(canvas, moon_sat2_x, moon_sat2_y, "L2", self.moon_sat2_buffer, False)
        self._draw_satellite(canvas, earth_sat_x, earth_sat_y, "E-S", self.earth_sat_buffer, False)
        
        sat_positions = {
            'mars': mars_pos,
            'mars_sat': (mars_sat_x, mars_sat_y),
            'moon_sat1': (moon_sat1_x, moon_sat1_y),
            'moon_sat2': (moon_sat2_x, moon_sat2_y),
            'earth_sat': (earth_sat_x, earth_sat_y),
            'earth': earth_pos,
        }
        self._sat_positions = sat_positions
        
        link_visible = [
            self.link0_visible,
            self.link1_visible,
            self.link2_visible,
            self.link3_visible,
            self.link4_visible,
            self.link5_visible,
        ]
        
        link_connections = [
            ('mars', 'mars_sat'),
            ('mars_sat', 'moon_sat1'),
            ('mars_sat', 'moon_sat2'),
            ('moon_sat1', 'earth_sat'),
            ('moon_sat2', 'earth_sat'),
            ('earth_sat', 'earth'),
        ]
        
        for link_idx, (from_key, to_key) in enumerate(link_connections):
            pos1 = sat_positions[from_key]
            pos2 = sat_positions[to_key]
            
            if self.transmitting_link == link_idx:
                self._draw_transmission_beam(canvas, pos1, pos2, self.transmit_progress)
            elif link_visible[link_idx]:
                self._draw_link_line(canvas, pos1, pos2, True)
        
        text = Text()
        for row in canvas:
            line = ''.join(row)
            colored_line = Text()
            i = 0
            while i < len(line):
                char = line[i]
                if char == 'M' and i + 3 < len(line) and line[i:i+4] == 'MARS':
                    colored_line.append('MARS', style='bold red')
                    i += 4
                elif char == 'M' and i + 2 < len(line) and line[i:i+3] == 'M-S':
                    colored_line.append('M-S', style='bold yellow')
                    i += 3
                elif char == 'M' and i + 2 < len(line) and line[i:i+3] == 'MOO':
                    colored_line.append('MOON', style='bold white')
                    i += 4
                elif char == 'L' and i + 1 < len(line) and line[i:i+2] in ['L1', 'L2']:
                    colored_line.append(line[i:i+2], style='bold yellow')
                    i += 2
                elif char == 'E' and i + 4 < len(line) and line[i:i+5] == 'EARTH':
                    style = 'bold red' if self.earth_antenna_off else 'bold cyan'
                    colored_line.append('EARTH', style=style)
                    i += 5
                elif char == 'E' and i + 2 < len(line) and line[i:i+3] == 'E-S':
                    colored_line.append('E-S', style='bold yellow')
                    i += 3
                elif char == '●':
                    colored_line.append('●', style='bold green')
                    i += 1
                elif char == '◉':
                    colored_line.append('◉', style='bold green blink')
                    i += 1
                elif char == '═' or char == '║':
                    colored_line.append(char, style='yellow')
                    i += 1
                elif char == '░':
                    colored_line.append(char, style='dim blue')
                    i += 1
                elif char == '▓':
                    colored_line.append(char, style='bold green')
                    i += 1
                elif char == '·':
                    colored_line.append(char, style='dim red')
                    i += 1
                elif char == '-':
                    colored_line.append(char, style='dim cyan')
                    i += 1
                elif char == '○':
                    colored_line.append(char, style='dim white')
                    i += 1
                elif char == '✖':
                    colored_line.append(char, style='bold red blink')
                    i += 1
                elif char == '[' or char == ']':
                    colored_line.append(char, style='magenta')
                    i += 1
                elif char.isdigit():
                    colored_line.append(char, style='bold magenta')
                    i += 1
                else:
                    colored_line.append(char)
                    i += 1
            
            text.append_text(colored_line)
            text.append('\n')
        
        return text
    
    def _draw_planet(self, canvas, cx, cy, name, short, radius, orbit_ry):
        for dy in range(-radius, radius + 1):
            for dx in range(-radius * 2, radius * 2 + 1):
                dist = math.sqrt((dx / 2) ** 2 + dy ** 2)
                if dist <= radius:
                    x, y = cx + dx, cy + dy
                    if 0 <= x < self.width and 0 <= y < self.height:
                        if dist > radius - 0.8:
                            canvas[y][x] = '○'
                        else:
                            canvas[y][x] = '·'
        
        label_y = cy + orbit_ry + 1
        name_start = cx - len(name) // 2
        if 0 <= label_y < self.height:
            for i, char in enumerate(name):
                x = name_start + i
                if 0 <= x < self.width:
                    canvas[label_y][x] = char
    
    def _draw_orbit_path(self, canvas, cx, cy, rx, ry):
        """Draw a dotted orbital path."""
        for angle in range(0, 360, 5):
            rad = math.radians(angle)
            x = int(cx + rx * math.cos(rad))
            y = int(cy + ry * math.sin(rad))
            if 0 <= x < self.width and 0 <= y < self.height:
                if canvas[y][x] == ' ':
                    canvas[y][x] = '·'
    
    def _draw_satellite(self, canvas, x, y, label, buffer_count, is_malicious=False):
        if 0 <= x < self.width and 0 <= y < self.height:
            if is_malicious:
                canvas[y][x] = '✖'
            elif buffer_count > 0:
                canvas[y][x] = '◉'
            else:
                canvas[y][x] = '●'
        
        label_start = x - len(label) // 2
        if 0 <= y - 1 < self.height:
            for i, char in enumerate(label):
                lx = label_start + i
                if 0 <= lx < self.width:
                    canvas[y - 1][lx] = char
        
        buf_str = f'[{buffer_count}]'
        buf_start = x - len(buf_str) // 2
        if 0 <= y + 1 < self.height:
            for i, char in enumerate(buf_str):
                lx = buf_start + i
                if 0 <= lx < self.width:
                    canvas[y + 1][lx] = char
    
    def _draw_link_line(self, canvas, pos1, pos2, is_connected):
        x1, y1 = pos1
        x2, y2 = pos2
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        steps = max(dx, dy)
        
        if steps == 0:
            return
        
        for i in range(0, steps + 1, 2):
            t = i / steps
            x = int(x1 + t * (x2 - x1))
            y = int(y1 + t * (y2 - y1))
            
            if 0 <= x < self.width and 0 <= y < self.height:
                if canvas[y][x] == ' ':
                    if is_connected:
                        canvas[y][x] = '-'
                    else:
                        canvas[y][x] = '·'
    
    def _draw_transmission_beam(self, canvas, pos1, pos2, progress):
        x1, y1 = pos1
        x2, y2 = pos2
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        steps = max(dx, dy)
        
        if steps == 0:
            return
        
        packet_pos = int(progress * steps)
        
        for i in range(0, steps + 1):
            t = i / steps
            x = int(x1 + t * (x2 - x1))
            y = int(y1 + t * (y2 - y1))
            
            if 0 <= x < self.width and 0 <= y < self.height:
                if canvas[y][x] == ' ':
                    if abs(i - packet_pos) <= 2:
                        canvas[y][x] = '▓'
                    else:
                        canvas[y][x] = '░'


class SpaceScenario(Screen):
    """Space scenario: Mars to Earth DTN communication with orbital animation."""
    
    BINDINGS = [
        ("q", "go_back", "Back to Menu"),
        ("s", "send_packet", "Send Bundle"),
        ("space", "toggle_pause", "Pause/Resume"),
    ]
    
    CSS = """
    SpaceScenario {
        background: #0a0a1a;
    }
    
    #main-container {
        width: 100%;
        height: 100%;
        padding: 1;
    }
    
    #orbital-view {
        width: 100%;
        height: 24;
        border: solid #334;
        background: #0a0a1a;
        padding: 0 1;
        content-align: center middle;
        text-align: center;
    }
    
    #status-panel {
        width: 100%;
        height: auto;
        border: solid blue;
        padding: 1;
        margin-top: 1;
    }
    
    #controls {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1;
    }
    
    #controls Button {
        margin: 0 1;
        background: #1a1a2e;
        border: solid white;
        color: white;
    }
    
    #controls Button:hover {
        background: #2a2a3e;
    }
    
    """
    
    is_paused: reactive[bool] = reactive(False)
    packets_sent: reactive[int] = reactive(0)
    packets_delivered: reactive[int] = reactive(0)
    packets_dropped: reactive[int] = reactive(0)
    
    blackhole_active: reactive[bool] = reactive(False)
    antenna_outage_active: reactive[bool] = reactive(False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_network()
        self._orbit_phase: float = 0.0
        self._transmitting_links: set[int] = set()
    
    def _setup_network(self) -> None:
        self.nodes = {
            "MA": Node("MA", "Mars", Buffer(max_size=5)),
            "MA-SAT": Node("MA-SAT", "Mars Satellite", Buffer(max_size=5)),
            "MO-SAT1": Node("MO-SAT1", "Moon Satellite 1 (L1)", Buffer(max_size=5)),
            "MO-SAT2": Node("MO-SAT2", "Moon Satellite 2 (L2)", Buffer(max_size=5)),
            "E-SAT": Node("E-SAT", "Earth Satellite", Buffer(max_size=5)),
            "E": Node("E", "Earth", Buffer(max_size=5)),
        }
        
        self.link_visible = [True, False, False, False, False, True]
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Vertical(id="main-container"):
            yield OrbitalView(id="orbital-view")
            with Horizontal(id="controls"):
                yield Button("Send Bundle [S]", id="send-btn", variant="primary")
                yield Button("Blackhole Attack", id="blackhole-btn")
                yield Button("Resource Exhaustion", id="exhaustion-btn")
                yield Button("Earth antenna: ON", id="outage-btn")
            
            yield Static(id="status-panel")
            

        
        yield Footer()
    
    def on_mount(self) -> None:
        self._update_display()
        self.run_simulation()
    
    @work(exclusive=True)
    async def run_simulation(self) -> None:
        while True:
            if not self.is_paused:
                await self._simulation_tick()
            await asyncio.sleep(0.016)
    
    async def _simulation_tick(self) -> None:
        self._orbit_phase += 0.002
        
        mars_sat_angle = self._orbit_phase * 1.5
        moon_sat1_angle = self._orbit_phase * 2.0
        moon_sat2_angle = self._orbit_phase * 2.0 + math.pi
        earth_sat_angle = self._orbit_phase * 1.8 + 0.5
        
        self.link_visible[0] = math.cos(mars_sat_angle) > 0.2
        
        mars_sat_facing_moon = math.cos(mars_sat_angle) > 0.3
        moon_sat1_facing_mars = math.cos(moon_sat1_angle) < -0.2
        self.link_visible[1] = mars_sat_facing_moon and moon_sat1_facing_mars
        
        moon_sat2_facing_mars = math.cos(moon_sat2_angle) < -0.2
        self.link_visible[2] = mars_sat_facing_moon and moon_sat2_facing_mars
        
        moon_sat1_facing_earth = math.cos(moon_sat1_angle) > 0.3
        earth_sat_facing_moon = math.cos(earth_sat_angle) < -0.2
        self.link_visible[3] = moon_sat1_facing_earth and earth_sat_facing_moon
        
        moon_sat2_facing_earth = math.cos(moon_sat2_angle) > 0.3
        self.link_visible[4] = moon_sat2_facing_earth and earth_sat_facing_moon
        
        if self.antenna_outage_active:
            self.link_visible[5] = False
        else:
            self.link_visible[5] = math.cos(earth_sat_angle) < 0.2
        
        try:
            orbital_view = self.query_one("#orbital-view", OrbitalView)
            orbital_view.orbit_phase = self._orbit_phase
            
            orbital_view.mars_sat_buffer = self.nodes["MA-SAT"].buffer_size
            orbital_view.moon_sat1_buffer = self.nodes["MO-SAT1"].buffer_size
            orbital_view.moon_sat2_buffer = self.nodes["MO-SAT2"].buffer_size
            orbital_view.earth_sat_buffer = self.nodes["E-SAT"].buffer_size
            
            orbital_view.moon_sat1_is_blackhole = self.blackhole_active
            orbital_view.earth_antenna_off = self.antenna_outage_active
            
            orbital_view.link0_visible = self.link_visible[0]
            orbital_view.link1_visible = self.link_visible[1]
            orbital_view.link2_visible = self.link_visible[2]
            orbital_view.link3_visible = self.link_visible[3]
            orbital_view.link4_visible = self.link_visible[4]
            orbital_view.link5_visible = self.link_visible[5]
        except Exception:
            pass
        
        await self._process_all_transmissions()
        
        self._update_display()
    
    async def _process_all_transmissions(self) -> None:
        routes = [
            ("MA", 0, "MA-SAT", self.link_visible[0]),
            ("MA-SAT", 1, "MO-SAT1", self.link_visible[1]),
            ("MA-SAT", 2, "MO-SAT2", self.link_visible[2]),
            ("MO-SAT1", 3, "E-SAT", self.link_visible[3]),
            ("MO-SAT2", 4, "E-SAT", self.link_visible[4]),
            ("E-SAT", 5, "E", self.link_visible[5]),
        ]
        
        for source_id, link_idx, target_id, is_visible in routes:
            if not is_visible or link_idx in self._transmitting_links:
                continue
            
            source_node = self.nodes[source_id]
            if source_node.buffer_size == 0:
                continue
            
            target_node = self.nodes[target_id]
            if target_id != "E" and target_node.buffer.is_full:
                continue
            
            packet = source_node.get_next_packet()
            if not packet:
                continue
            
            self._animate_transmission(link_idx, source_id, target_id, packet)
    
    @work(exclusive=False)
    async def _animate_transmission(self, link_idx: int, source_id: str, target_id: str, packet: Packet) -> None:
        self._transmitting_links.add(link_idx)
        
        try:
            orbital_view = self.query_one("#orbital-view", OrbitalView)
            orbital_view.transmitting_link = link_idx
            
            for progress in range(0, 101, 2):
                orbital_view.transmit_progress = progress / 100.0
                await asyncio.sleep(0.015)
            
            orbital_view.transmitting_link = -1
            orbital_view.transmit_progress = 0.0
        except Exception:
            await asyncio.sleep(0.5)
        
        target_node = self.nodes[target_id]
        
        if target_id == "MO-SAT1" and self.blackhole_active:
            self.packets_dropped += 1
        elif target_id == "E":
            self.packets_delivered += 1
        else:
            target_node.queue_packet(packet)
        
        self._transmitting_links.discard(link_idx)
    
    def _update_display(self) -> None:
        try:
            status = self.query_one("#status-panel", Static)
            
            table = Table.grid(padding=(0, 2))
            table.add_column(justify="left")
            table.add_column(justify="center")
            table.add_column(justify="center")
            table.add_column(justify="right")
            
            mars_l1 = "🟢 VISIBLE" if self.link_visible[1] else "🔴 BLOCKED"
            mars_l2 = "🟢 VISIBLE" if self.link_visible[2] else "🔴 BLOCKED"
            l1_earth = "🟢 VISIBLE" if self.link_visible[3] else "🔴 BLOCKED"
            l2_earth = "🟢 VISIBLE" if self.link_visible[4] else "🔴 BLOCKED"
            
            table.add_row(
                Text(f"Sent: {self.packets_sent}", style="cyan"),
                Text(f"M-SAT→L1: {mars_l1}", style="white"),
                Text(f"M-SAT→L2: {mars_l2}", style="white"),
                Text(f"Delivered: {self.packets_delivered} | Dropped: {self.packets_dropped}", style="green bold"),
            )
            
            table.add_row(
                Text("", style=""),
                Text(f"L1→E-SAT: {l1_earth}", style="white"),
                Text(f"L2→E-SAT: {l2_earth}", style="white"),
                Text("", style=""),
            )
            
            total_buffered = sum(node.buffer_size for node in self.nodes.values())
            state = "PAUSED" if self.is_paused else ("TRANSMITTING" if len(self._transmitting_links) > 0 else "ACTIVE")
            
            mars_status = f"Mars: {self.nodes['MA'].buffer_size}/5"
            mars_sat_status = f"M-SAT: {self.nodes['MA-SAT'].buffer_size}/5"
            
            table.add_row(
                Text(mars_status, style="yellow"),
                Text(mars_sat_status, style="yellow"),
                Text(f"Total Buffered: {total_buffered}", style="yellow"),
                Text(f"State: {state}", style="magenta bold"),
            )
            
            status.update(Panel(table, title="📡 Mission Control", border_style="blue"))
        except Exception:
            pass
        

    

    
    def action_send_packet(self) -> None:
        mars_node = self.nodes["MA"]
        if not mars_node.buffer.is_full:
            packet = Packet("MA", "E", PacketType.NORMAL, f"Data-{self.packets_sent}")
            if mars_node.queue_packet(packet):
                self.packets_sent += 1
    
    def action_toggle_pause(self) -> None:
        self.is_paused = not self.is_paused
    
    def action_go_back(self) -> None:
        self.app.pop_screen()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-btn":
            self.action_send_packet()
        elif event.button.id == "blackhole-btn":
            self.toggle_blackhole_attack()
        elif event.button.id == "exhaustion-btn":
            self.trigger_resource_exhaustion()
        elif event.button.id == "outage-btn":
            self.toggle_antenna_outage()
    
    def toggle_blackhole_attack(self) -> None:
        self.blackhole_active = not self.blackhole_active
        
        try:
            btn = self.query_one("#blackhole-btn", Button)
            if self.blackhole_active:
                btn.label = "Blackhole: ON"
                self.nodes["MO-SAT1"].buffer.clear()
            else:
                btn.label = "Blackhole Attack"
            btn.refresh()
        except Exception:
            pass
    
    def trigger_resource_exhaustion(self) -> None:
        l1_node = self.nodes["MO-SAT1"]
        l2_node = self.nodes["MO-SAT2"]
        
        if not l1_node.buffer.is_full:
            spam_packet = Packet("ATTACKER", "SPAM", PacketType.NORMAL, "spam")
            l1_node.queue_packet(spam_packet)
        
        if not l2_node.buffer.is_full:
            spam_packet = Packet("ATTACKER", "SPAM", PacketType.NORMAL, "spam")
            l2_node.queue_packet(spam_packet)
    
    def toggle_antenna_outage(self) -> None:
        self.antenna_outage_active = not self.antenna_outage_active
        
        try:
            btn = self.query_one("#outage-btn", Button)
            if self.antenna_outage_active:
                btn.label = "Earth antenna: OFF"
            else:
                btn.label = "Earth antenna: ON"
            btn.refresh()
        except Exception:
            pass
