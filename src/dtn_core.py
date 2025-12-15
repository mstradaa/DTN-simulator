"""Packet, Buffer, and Node classes for DTN simulation."""

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Iterator, Callable
import time
import uuid


class PacketType(Enum):
    NORMAL = "normal"


@dataclass
class Packet:
    """Represents a DTN packet with store-and-forward capability."""
    
    source: str
    destination: str
    packet_type: PacketType = PacketType.NORMAL
    payload: str = ""
    packet_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: float = field(default_factory=time.time)
    hops: list[str] = field(default_factory=list)
    
    @property
    def age(self) -> float:
        return time.time() - self.created_at
    
    def add_hop(self, node_id: str) -> None:
        self.hops.append(node_id)
    
    def __repr__(self) -> str:
        return f"[{self.packet_id}]"


class Buffer:
    """FIFO buffer for DTN packets."""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._queue: deque[Packet] = deque()
    
    @property
    def size(self) -> int:
        return len(self._queue)
    
    @property
    def is_empty(self) -> bool:
        return self.size == 0
    
    @property
    def is_full(self) -> bool:
        return self.size >= self.max_size
    
    def enqueue(self, packet: Packet) -> bool:
        if self.is_full:
            return False
        self._queue.append(packet)
        return True
    
    def dequeue(self) -> Optional[Packet]:
        if self._queue:
            return self._queue.popleft()
        return None
    
    def peek(self) -> Optional[Packet]:
        if self._queue:
            return self._queue[0]
        return None
    
    def clear(self) -> int:
        count = self.size
        self._queue.clear()
        return count
    
    def __iter__(self) -> Iterator[Packet]:
        yield from self._queue
    
    def __len__(self) -> int:
        return self.size
    
    def __repr__(self) -> str:
        return f"Buffer({self.size}/{self.max_size})"


@dataclass
class Node:
    """Represents a DTN node with buffering capability."""
    
    node_id: str
    name: str
    buffer: Buffer = field(default_factory=Buffer)
    is_online: bool = True
    _connections: dict[str, bool] = field(default_factory=dict)
    on_receive: Optional[Callable[[Packet], None]] = None
    
    def add_connection(self, other_node_id: str, in_range: bool = False) -> None:
        self._connections[other_node_id] = in_range
    
    def set_in_range(self, other_node_id: str, in_range: bool) -> None:
        if other_node_id in self._connections:
            self._connections[other_node_id] = in_range
    
    def is_in_range(self, other_node_id: str) -> bool:
        return self._connections.get(other_node_id, False)
    
    def get_connected_nodes(self) -> list[str]:
        return [nid for nid, in_range in self._connections.items() if in_range]
    
    def queue_packet(self, packet: Packet) -> bool:
        if not self.is_online:
            return False
        return self.buffer.enqueue(packet)
    
    def receive_packet(self, packet: Packet) -> bool:
        if not self.is_online:
            return False
        
        packet.add_hop(self.node_id)
        
        if packet.destination == self.node_id:
            if self.on_receive:
                self.on_receive(packet)
            return True
        else:
            return self.queue_packet(packet)
    
    def get_next_packet(self) -> Optional[Packet]:
        if not self.is_online:
            return None
        return self.buffer.dequeue()
    
    def peek_next_packet(self) -> Optional[Packet]:
        return self.buffer.peek()
    
    @property
    def buffer_size(self) -> int:
        return self.buffer.size
    
    def set_online(self, online: bool) -> None:
        self.is_online = online
    
    def __repr__(self) -> str:
        status = "ON" if self.is_online else "OFF"
        return f"Node({self.node_id}:{self.name} [{status}] buf={self.buffer_size})"
