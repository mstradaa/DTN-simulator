"""Military convoy scenario for DTN simulation."""

import asyncio
import random
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


class ConvoyView(Static):
    """A unified view showing vehicles on an animated road."""
    
    road_frame: reactive[int] = reactive(0)
    
    v1_buffer: reactive[int] = reactive(0)
    v2_buffer: reactive[int] = reactive(0)
    v3_buffer: reactive[int] = reactive(0)
    v3_online: reactive[bool] = reactive(True)
    
    v1_receiving: reactive[bool] = reactive(False)
    v2_receiving: reactive[bool] = reactive(False)
    v3_receiving: reactive[bool] = reactive(False)
    cp_receiving: reactive[bool] = reactive(False)
    
    v1_v2_connected: reactive[bool] = reactive(True)
    v2_v3_connected: reactive[bool] = reactive(True)
    v3_cp_connected: reactive[bool] = reactive(False)
    
    transmitting_link: reactive[int] = reactive(-1)
    transmit_progress: reactive[float] = reactive(0.0)
    
    cp_delivered: reactive[int] = reactive(0)
    cp_show_ack: reactive[bool] = reactive(False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.width = 95
    
    def render(self) -> Text:
        text = Text()
        
        v1_style = "cyan"
        v2_style = "cyan"  
        v3_style = "dim red" if not self.v3_online else "cyan"
        hq_style = "bold yellow"
        
        box_w = 13
        gap_w = 6
        hq_w = 16
        
        def center_in(s: str, width: int) -> str:
            visual_len = len(s)
            for c in s:
                if ord(c) > 0x1F000:
                    visual_len += 1
            pad_total = width - visual_len
            pad_left = pad_total // 2
            pad_right = pad_total - pad_left
            return " " * pad_left + s + " " * pad_right
        
        offset = self.road_frame % 6
        road_line = ""
        road_width = box_w * 3 + gap_w * 3 + hq_w
        for i in range(road_width):
            if (i - offset) % 6 < 3:
                road_line += "═"
            else:
                road_line += " "
        text.append(road_line, style="white bold")
        text.append("\n")
        
        v1_icon = "📡" if self.v1_receiving else "✓"
        v2_icon = "📡" if self.v2_receiving else "✓"
        v3_icon = "⛔" if not self.v3_online else ("📡" if self.v3_receiving else "✓")
        hq_s = "✓" if self.cp_show_ack else " "
        
        v1_s = f"{v1_icon} B:{self.v1_buffer}"
        v2_s = f"{v2_icon} B:{self.v2_buffer}"
        v3_s = f"{v3_icon} B:{self.v3_buffer}"
        
        status_line = Text()
        status_line.append(center_in(v1_s, box_w), style="green")
        status_line.append(" " * gap_w)
        status_line.append(center_in(v2_s, box_w), style="green")
        status_line.append(" " * gap_w)
        status_line.append(center_in(v3_s, box_w), style="green" if self.v3_online else "red")
        status_line.append(" " * gap_w)
        status_line.append(center_in(hq_s, hq_w), style="green")
        status_line.append("\n")
        text.append_text(status_line)
        
        row1 = Text()
        row1.append("┌───────────┐", style=v1_style)
        row1.append(" " * gap_w)
        row1.append("┌───────────┐", style=v2_style)
        row1.append(" " * gap_w)
        row1.append("┌───────────┐", style=v3_style)
        row1.append(" " * gap_w)
        row1.append("┌──────────────┐", style=hq_style)
        row1.append("\n")
        text.append_text(row1)
        
        row2 = Text()
        row2.append("│  V1 LEAD  │", style=v1_style)
        
        if self.transmitting_link == 0:
            link_len = gap_w
            packet_pos = int(self.transmit_progress * link_len)
            link_str = ""
            for i in range(link_len):
                if abs(i - packet_pos) <= 1:
                    link_str += "▓"
                else:
                    link_str += "░"
            row2.append(link_str, style="bold green")
        elif self.v1_v2_connected:
            row2.append("──────", style="dim green")
        else:
            row2.append("· · · ", style="dim red")
        
        row2.append("│ V2 CARGO  │", style=v2_style)
        
        if self.transmitting_link == 1:
            link_len = gap_w
            packet_pos = int(self.transmit_progress * link_len)
            link_str = ""
            for i in range(link_len):
                if abs(i - packet_pos) <= 1:
                    link_str += "▓"
                else:
                    link_str += "░"
            row2.append(link_str, style="bold green")
        elif self.v2_v3_connected:
            row2.append("──────", style="dim green")
        else:
            row2.append("· · · ", style="dim red")
        
        row2.append("│ V3 COMMS  │", style=v3_style)
        
        if self.transmitting_link == 2:
            link_len = gap_w
            packet_pos = int(self.transmit_progress * link_len)
            link_str = ""
            for i in range(link_len):
                if abs(i - packet_pos) <= 1:
                    link_str += "▓"
                else:
                    link_str += "░"
            row2.append(link_str, style="bold green")
        elif self.v3_cp_connected:
            row2.append("──────", style="dim green")
        else:
            row2.append("· · · ", style="dim red")
        
        row2.append("│ HEAD QUARTER │", style=hq_style)
        row2.append("\n")
        text.append_text(row2)
        
        row3 = Text()
        row3.append("└─────◊─────┘", style=v1_style)
        row3.append(" " * gap_w)
        row3.append("└───────────┘", style=v2_style)
        row3.append(" " * gap_w)
        row3.append("└─────◊─────┘", style=v3_style)
        row3.append(" " * gap_w)
        row3.append("└──────────────┘", style=hq_style)
        row3.append("\n")
        text.append_text(row3)
        
        buff_row = Text()
        v1_b = f"[{self._make_buffer_bar(self.v1_buffer)}]"
        v2_b = f"[{self._make_buffer_bar(self.v2_buffer)}]"
        v3_b = f"[{self._make_buffer_bar(self.v3_buffer)}]"
        hq_delivered = f"✓ {self.cp_delivered}"
        
        buff_row.append(center_in(v1_b, box_w), style=self._buffer_color(self.v1_buffer))
        buff_row.append(" " * gap_w)
        buff_row.append(center_in(v2_b, box_w), style=self._buffer_color(self.v2_buffer))
        buff_row.append(" " * gap_w)
        buff_row.append(center_in(v3_b, box_w), style=self._buffer_color(self.v3_buffer) if self.v3_online else "red")
        buff_row.append(" " * gap_w)
        buff_row.append(center_in(hq_delivered, hq_w), style="bold green")
        buff_row.append("\n")
        text.append_text(buff_row)
        

        
        offset = self.road_frame % 6
        road_line = ""
        road_width = box_w * 3 + gap_w * 3 + hq_w
        for i in range(road_width):
            if (i - offset) % 6 < 3:
                road_line += "═"
            else:
                road_line += " "
        
        text.append(road_line, style="white bold")
        text.append("\n")
        
        return text
    
    def _make_buffer_bar(self, count):
        bar_len = 6
        filled = min(count, bar_len)
        return "█" * filled + "░" * (bar_len - filled)
    
    def _buffer_color(self, count):
        if count < 3:
            return "green"
        elif count < 5:
            return "yellow"
        else:
            return "red"


class MilitaryScenario(Screen):
    """Military convoy DTN scenario."""
    
    BINDINGS = [
        ("q", "go_back", "Back to Menu"),
        ("t", "toggle_v3", "Toggle V3 Jamming"),
        ("s", "send_packet", "Send Bundle"),
        ("space", "toggle_pause", "Pause/Resume"),
    ]
    
    CSS = """
    MilitaryScenario {
        background: $surface;
    }
    
    #main-container {
        width: 100%;
        height: 100%;
        padding: 1;
        align: center middle;
    }
    
    #convoy-view {
        width: 100%;
        height: 16;
        border: solid $primary;
        padding: 0 1;
        margin-bottom: 1;
        content-align: center middle;
        text-align: center;
    }
    
    #status-panel {
        width: 100%;
        height: auto;
        border: solid blue;
        padding: 1;
        content-align: center middle;
        text-align: center;
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
    v3_online: reactive[bool] = reactive(True)
    packets_created: reactive[int] = reactive(0)
    packets_delivered: reactive[int] = reactive(0)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_network()
        self._road_frame = 0
        self._transfer_in_progress = False
        
        self._range_states = {
            "v1_v2": True,
            "v2_v3": True,
            "v3_cp": False,
        }
        self._range_timers = {
            "v1_v2": 0,
            "v2_v3": 0,
            "v3_cp": 0,
        }
    
    def _setup_network(self) -> None:
        self.vehicles = {
            "V1": Node("V1", "Lead Vehicle"),
            "V2": Node("V2", "Cargo Vehicle"),
            "V3": Node("V3", "Comms Vehicle"),
            "HQ": Node("HQ", "Head Quarter"),
        }
        
        self.vehicles["V1"].add_connection("V2", True)
        self.vehicles["V2"].add_connection("V1", True)
        self.vehicles["V2"].add_connection("V3", True)
        self.vehicles["V3"].add_connection("V2", True)
        self.vehicles["V3"].add_connection("HQ", False)
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Vertical(id="main-container"):
            yield ConvoyView(id="convoy-view")
            with Horizontal(id="controls"):
                yield Button("Send Bundle [S]", id="send-btn", variant="primary")
                yield Button("V3 Jamming: OFF", id="toggle-btn")
            
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
            await asyncio.sleep(0.1)
    
    async def _simulation_tick(self) -> None:
        self._road_frame += 1
        try:
            convoy = self.query_one("#convoy-view", ConvoyView)
            convoy.road_frame = self._road_frame
        except Exception:
            pass
        
        self._update_range_states()
        self._update_convoy_view()
        self._process_forwarding()
        self._update_display()
    
    def _update_range_states(self) -> None:
        self._range_states["v1_v2"] = True
        
        if self.v3_online:
            self._range_states["v2_v3"] = True
        else:
            self._range_states["v2_v3"] = False
        
        self._range_timers["v3_cp"] += 1
        if self.v3_online:
            if self._range_timers["v3_cp"] > random.randint(40, 60):
                self._range_states["v3_cp"] = not self._range_states["v3_cp"]
                self._range_timers["v3_cp"] = 0
        else:
            self._range_states["v3_cp"] = False
    
    def _update_convoy_view(self) -> None:
        try:
            convoy = self.query_one("#convoy-view", ConvoyView)
            convoy.v1_buffer = self.vehicles["V1"].buffer_size
            convoy.v2_buffer = self.vehicles["V2"].buffer_size
            convoy.v3_buffer = self.vehicles["V3"].buffer_size
            convoy.v3_online = self.v3_online
            convoy.v1_v2_connected = self._range_states["v1_v2"]
            convoy.v2_v3_connected = self._range_states["v2_v3"]
            convoy.v3_cp_connected = self._range_states["v3_cp"]
            convoy.cp_delivered = self.packets_delivered
        except Exception:
            pass
    
    def _process_forwarding(self) -> None:
        if self._transfer_in_progress:
            return
        
        if self._range_states["v1_v2"] and self.vehicles["V1"].buffer_size > 0:
            self._start_transfer("V1", "V2", 0)
        elif self._range_states["v2_v3"] and self.v3_online and self.vehicles["V2"].buffer_size > 0:
            self._start_transfer("V2", "V3", 1)
        elif self._range_states["v3_cp"] and self.v3_online and self.vehicles["V3"].buffer_size > 0:
            self._start_hq_delivery()
    
    def _start_transfer(self, from_id: str, to_id: str, link_index: int) -> None:
        packet = self.vehicles[from_id].get_next_packet()
        if not packet:
            return
        
        self._transfer_in_progress = True
        self._do_transfer_animation(packet, from_id, to_id, link_index)
    
    @work(exclusive=False)
    async def _do_transfer_animation(self, packet, from_id: str, to_id: str, link_index: int) -> None:
        try:
            convoy = self.query_one("#convoy-view", ConvoyView)
            convoy.transmitting_link = link_index
            
            if to_id == "V2":
                convoy.v2_receiving = True
            elif to_id == "V3":
                convoy.v3_receiving = True
            
            for progress in range(0, 101, 1):
                convoy.transmit_progress = progress / 100.0
                await asyncio.sleep(0.03)
            
            convoy.transmitting_link = -1
            convoy.transmit_progress = 0.0
            convoy.v2_receiving = False
            convoy.v3_receiving = False
            
            self.vehicles[to_id].queue_packet(packet)
            self._update_convoy_view()
        except Exception:
            pass
        finally:
            self._transfer_in_progress = False
    
    def _start_hq_delivery(self) -> None:
        packet = self.vehicles["V3"].get_next_packet()
        if not packet:
            return
        
        self._transfer_in_progress = True
        self._do_hq_delivery_animation(packet)
    
    @work(exclusive=False)
    async def _do_hq_delivery_animation(self, packet) -> None:
        try:
            convoy = self.query_one("#convoy-view", ConvoyView)
            convoy.transmitting_link = 2
            convoy.cp_receiving = True
            
            for progress in range(0, 101, 1):
                convoy.transmit_progress = progress / 100.0
                await asyncio.sleep(0.03)
            
            convoy.transmitting_link = -1
            convoy.transmit_progress = 0.0
            convoy.cp_receiving = False
            
            self.packets_delivered += 1
            convoy.cp_delivered = self.packets_delivered
            convoy.cp_show_ack = True
            await asyncio.sleep(0.3)
            convoy.cp_show_ack = False
            self._update_convoy_view()
        except Exception:
            pass
        finally:
            self._transfer_in_progress = False
    
    def _update_display(self) -> None:
        self._update_convoy_view()
        
        try:
            status = self.query_one("#status-panel", Static)
            
            table = Table.grid(padding=(0, 2))
            table.add_column(justify="left")
            table.add_column(justify="center")
            table.add_column(justify="center")
            table.add_column(justify="right")
            
            c1 = "🟢" if self._range_states["v1_v2"] else "🔴"
            c2 = "🟢" if self._range_states["v2_v3"] else "🔴"
            c3 = "🟢" if self._range_states["v3_cp"] else "🔴"
            
            v3_status = "🟢 ONLINE" if self.v3_online else "🔴 OFFLINE"
            
            table.add_row(
                Text(f"V1↔V2: {c1}", style="white"),
                Text(f"V2↔V3: {c2}", style="white"),
                Text(f"V3↔HQ: {c3}", style="white"),
                Text(f"V3 Status: {v3_status}", style="bold"),
            )
            
            total_buffer = sum(v.buffer_size for v in self.vehicles.values())
            state = "PAUSED" if self.is_paused else "RUNNING"
            
            table.add_row(
                Text(f"Bundles Created: {self.packets_created}", style="cyan"),
                Text(f"Total Buffered: {total_buffer}", style="yellow"),
                Text(f"Delivered: {self.packets_delivered}", style="green bold"),
                Text(f"State: {state}", style="magenta"),
            )
            
            status.update(Panel(table, title="Convoy Status", border_style="blue"))
        except Exception:
            pass
        

    

    
    def action_send_packet(self) -> None:
        packet = Packet("V1", "HQ", PacketType.NORMAL, f"Data-{self.packets_created}")
        self.vehicles["V1"].queue_packet(packet)
        self.packets_created += 1
        self._update_convoy_view()
    
    def action_toggle_v3(self) -> None:
        self.v3_online = not self.v3_online
        self.vehicles["V3"].set_online(self.v3_online)
        
        try:
            btn = self.query_one("#toggle-btn", Button)
            if self.v3_online:
                btn.label = "V3 Jamming: OFF"
            else:
                btn.label = "V3 Jamming: ON"
            btn.refresh()
        except Exception:
            pass
        
        if self.v3_online:
            pass
        else:
            self._range_states["v2_v3"] = False
            self._range_states["v3_cp"] = False
        
        self._update_convoy_view()
        self._update_display()
    
    def action_toggle_pause(self) -> None:
        self.is_paused = not self.is_paused
    
    def action_go_back(self) -> None:
        self.app.pop_screen()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-btn":
            self.action_send_packet()
        elif event.button.id == "toggle-btn":
            self.action_toggle_v3()
