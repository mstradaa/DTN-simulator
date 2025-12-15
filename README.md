<p align="center">
  <img width="250" height="137" alt="DTN-logo" src="https://github.com/user-attachments/assets/de8cc209-bb88-457f-8fac-7e95ca1ac1d0" />
</p>

# Delay Tolerant Network (DTN) Simulation

This project provides an interactive simulation of Delay and Disruption Tolerant Networks (DTNs). 

It demonstrates DTN behaviors such as store-and-forward routing, intermittent connectivity, and buffering through a Terminal User Interface (TUI).
The simulator also supports different DTN attacks such as black hole attacks (traffic dropping) and resource exhaustion.

For a deeper explanation of DTN theory, protocols, and security concepts, see the dedicated blog post [here](https://mstrada.me/posts/dtnsec).

## Simulation Scenarios

The program includes two different scenarios:

### 1) Space Communications (Mars to Earth)
<img width="1326" height="550" alt="DTN-space" src="https://github.com/user-attachments/assets/4aa0dfba-73b5-4ce9-b906-a5d13a45238c" />

This scenario simulates high-latency space transmission from a research outpost on Mars to Mission Control on Earth. 

Direct communication can be unavailable due to obstructions and timing constraints, so the network relies on relays (Mars Orbiter, Lunar Satellites, Earth Satellite). \
It uses opportunistic communication where satellites discover each other at runtime via beacons, and the contact duration is uncertain.

For this simulation, the program simulates Mars transmission only when the satellite is on the right side.

The scenario allows activation of three different attacks:

- Black hole attack: a malicious (or compromised) DTN node advertises itself as a good relay, accepts bundles, and then silently drops them instead of forwarding. This reduces delivery rates and can create “missing data” even when contacts occur.
- Resource exhaustion: this attack can be activated on L1 and L2 satellites, draining their storage capacity  and forcing them to drop packets.
- Earth Mission Control Outage: this attack simulates a failure of the Earth satellite, which must wait to transmit and use its storage.

> [!NOTE]
> This project does **not** simulate realistic orbital paths, speeds, or link budgets. The focus is to demonstrate DTN concepts using two example use cases with a deliberately simple visual representation.

### 2) Military Communications (Tactical Convoy)
<img width="1326" height="427" alt="DTN-military" src="https://github.com/user-attachments/assets/bc1cc55c-954f-4ae9-9ac2-fa23a90cf611" />

This scenario represents an environment where a military convoy moves through hostile territory. \
The goal is to transport a sensitive status report from the Lead Vehicle to the Head Quarter (HQ) while avoiding unnecessary transmission.

The transmission uses persistent contacts between the three vehicles, while utilizing opportunistic contacts with the HQ due to possible environmental obstructions. \
Data moves physically with the convoy (Lead → Cargo → Rear). After forwarding, a node deletes its local copy. 

The scenario allows the activation of a jamming attack on the rear truck (comms sender) and the usage of persistent storage by the previous vehicle until the jamming attack is over.

## Prerequisites

- Python ≥ 3.10
- textual ≥ 0.40.0
- rich ≥ 13.0.0

## Project Structure

```
dtn-simulation/
├── main.py          # Main application entry point
├── src/
│   ├── dtn_core.py  # Core DTN classes (Packet, Buffer, Node)
│   ├── menu.py      # Main menu screen
│   ├── space.py     # Space scenario implementation
│   └── military.py  # Military convoy scenario implementation
├── requirements.txt # Python dependencies
└── README.md        # This file
```
