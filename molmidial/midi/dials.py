#!/usr/bin/env python3
"""
MIDI Dials Test/Demo Script
===========================

This is a simple test script for MIDI input in ElMo.
For full MIDI integration, use the MIDIController class and MIDIControlWidget.
"""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import mido
    import rtmidi

    MIDI_AVAILABLE = True
    print("✅ MIDI libraries available")
    print(f"rtmidi: {rtmidi}")
    print(f"rtmidi type: {type(rtmidi)}")
    print(f"rtmidi file: {getattr(rtmidi, '__file__', 'NO __file__ ATTR')}")
    print(
        f"API_UNSPECIFIED: {getattr(rtmidi, 'API_UNSPECIFIED', 'NO API_UNSPECIFIED')}"
    )
    print(
        f"Available functions: {[attr for attr in dir(rtmidi) if not attr.startswith('_')]}"
    )

    # Test if we can actually use mido
    try:
        ports = mido.get_input_names()
        print(f"✅ MIDI ports test successful: {len(ports)} ports found")
    except Exception as e:
        print(f"⚠️ MIDI port test failed: {e}")
        # Try alternative backend
        try:
            mido.set_backend("mido.backends.portmidi")
            ports = mido.get_input_names()
            print(f"✅ Alternative MIDI backend successful: {len(ports)} ports found")
        except Exception as e2:
            print(f"❌ Alternative MIDI backend also failed: {e2}")
            MIDI_AVAILABLE = False

except ImportError as e:
    MIDI_AVAILABLE = False
    print(f"❌ MIDI libraries not available: {e}")
    print("Install with: pip install mido rtmidi")


def list_midi_ports():
    """List available MIDI input ports"""
    if not MIDI_AVAILABLE:
        print("❌ MIDI not available")
        return []

    print("Available MIDI input ports:")
    ports = mido.get_input_names()
    for i, name in enumerate(ports):
        print(f"  {i}: {name}")
    return ports


def listen_to_controller(port_name):
    """Listen to MIDI control change messages from a specific port"""
    if not MIDI_AVAILABLE:
        print("❌ MIDI not available")
        return

    print(f"Connecting to MIDI input: {port_name}")
    try:
        with mido.open_input(port_name) as inport:
            print(
                "Listening for incoming MIDI control change messages (press Ctrl+C to stop)..."
            )
            print("Format: Time | Channel | Controller | Value")
            print("-" * 50)

            for msg in inport:
                if msg.type == "control_change":
                    print(
                        f"{msg.time:8.3f} | Channel {msg.channel+1:2d} | "
                        f"Controller {msg.control:3d} | Value {msg.value:3d}"
                    )
                elif msg.type == "note_on":
                    print(
                        f"{msg.time:8.3f} | Note ON  | Channel {msg.channel+1:2d} | "
                        f"Note {msg.note:3d} | Velocity {msg.velocity:3d}"
                    )
                elif msg.type == "note_off":
                    print(
                        f"{msg.time:8.3f} | Note OFF | Channel {msg.channel+1:2d} | "
                        f"Note {msg.note:3d} | Velocity {msg.velocity:3d}"
                    )
    except KeyboardInterrupt:
        print("\nStopped listening.")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_elmo_midi_controller():
    """Test the ElMo MIDI controller"""
    print("\n🧪 Testing ElMo MIDI Controller...")

    try:
        from elmo.midi.controller import MIDIController, create_elmo_midi_controller

        # Create a basic controller
        controller = MIDIController()

        # List available ports
        ports = controller.list_available_ports()
        print(f"Found {len(ports)} MIDI ports")

        # Show mappings
        mappings = controller.get_mapping_info()
        print(f"Default mappings: {len(mappings)}")
        for name, info in mappings.items():
            print(
                f"  {name}: Control {info['control_number']} -> {info['target_function']}"
            )

        return controller

    except Exception as e:
        print(f"❌ Error testing MIDI controller: {e}")
        return None


if __name__ == "__main__":
    print("🎛️ ElMo MIDI Dials Test Script")
    print("=" * 40)

    # Test MIDI availability
    if not MIDI_AVAILABLE:
        print("❌ MIDI libraries not available. Install with: pip install mido rtmidi")
        sys.exit(1)

    # List available ports
    ports = list_midi_ports()

    if not ports:
        print("❌ No MIDI ports found")
        sys.exit(1)

    # Test ElMo MIDI controller
    controller = test_elmo_midi_controller()

    # Interactive mode
    print("\n" + "=" * 40)
    print("Interactive MIDI Listening")
    print("=" * 40)

    try:
        port_index = input(
            f"Enter port number (0-{len(ports)-1}) or 'q' to quit: "
        ).strip()

        if port_index.lower() == "q":
            print("Goodbye!")
            sys.exit(0)

        try:
            port_num = int(port_index)
            if 0 <= port_num < len(ports):
                port_name = ports[port_num]
                listen_to_controller(port_name)
            else:
                print("❌ Invalid port number")
        except ValueError:
            print("❌ Invalid input")

    except KeyboardInterrupt:
        print("\nGoodbye!")
