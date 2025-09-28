"""
MIDI Controller for ElMo
========================

This module provides MIDI control integration for ElMo dials and controls.
It allows mapping MIDI control change messages to various ElMo parameters.
"""

import threading
import time
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, List

from molmidial.midi.dial.settings import DialSettings
from molmidial.logger import Logger as log

try:
    import mido
    import rtmidi

    # Check if rtmidi has the required API
    if hasattr(rtmidi, "API_UNSPECIFIED"):
        MIDI_AVAILABLE = True
    else:
        # Try to use mido without rtmidi backend
        mido.set_backend("mido.backends.portmidi")
        MIDI_AVAILABLE = True
except ImportError:
    MIDI_AVAILABLE = False
    mido = None
    rtmidi = None
except Exception as e:
    # Handle rtmidi compatibility issues
    try:
        mido.set_backend("mido.backends.portmidi")
        MIDI_AVAILABLE = True
        rtmidi = None  # Don't use rtmidi if it has compatibility issues
    except:
        MIDI_AVAILABLE = False
        mido = None
        rtmidi = None


class MIDIControlType(Enum):
    """Types of MIDI controls available"""

    DIAL = "dial"
    SLIDER = "slider"
    BUTTON = "button"
    KNOB = "knob"
    FADER = "fader"


@dataclass
class MIDIMapping:
    """Configuration for a MIDI control mapping"""

    control_number: int
    channel: int
    control_type: MIDIControlType
    target_function: str
    min_value: float = 0.0
    max_value: float = 127.0
    target_min: float = 0.0
    target_max: float = 1.0
    enabled: bool = True
    description: str = ""


class MIDIController:
    """
    Main MIDI controller class for ElMo.

    Handles MIDI input, control mapping, and integration with ElMo's dial system.
    """

    def __init__(self, main_window=None):
        self.main_window = main_window
        self.is_running = False
        self.midi_input = None
        self.midi_thread = None
        self.mappings: Dict[str, MIDIMapping] = {}
        self.control_handlers: Dict[str, Callable] = {}

        # Throttling for rapid MIDI updates
        self._last_update_times = defaultdict(float)
        self._throttle_interval = 0.05  # 50ms minimum between updates for same control
        self._last_values = {}

        # Special throttling for expensive operations
        self._expensive_controls = {
            "connolly_transparency": 0.2,  # 200ms for Connolly surface
            "connolly_probe_radius": 0.2,  # 200ms for Connolly surface
            "isosurface_level": 0.1,  # 100ms for isosurface
        }

        # Default MIDI mappings
        self._setup_default_mappings()

        # Available MIDI ports
        self.available_ports = []
        self.current_port = None

        if not MIDI_AVAILABLE:
            log.warning(
                "⚠️ MIDI libraries not available. Install mido and rtmidi for MIDI support."
            )

    def _setup_default_mappings(self):
        """Set up default MIDI control mappings"""
        # Camera controls
        self.add_mapping(
            "zoom",
            MIDIMapping(
                control_number=1,  # Mod wheel
                channel=0,
                control_type=MIDIControlType.KNOB,
                target_function="camera_zoom",
                target_min=DialSettings.ZOOM.min,
                target_max=DialSettings.ZOOM.max,
                description="Camera Zoom",
            ),
        )

        self.add_mapping(
            "rotation_x",
            MIDIMapping(
                control_number=2,
                channel=0,
                control_type=MIDIControlType.KNOB,
                target_function="camera_rot_x",
                target_min=DialSettings.ROT_X.min,
                target_max=DialSettings.ROT_X.max,
                description="X Rotation",
            ),
        )

        self.add_mapping(
            "rotation_y",
            MIDIMapping(
                control_number=3,
                channel=0,
                control_type=MIDIControlType.KNOB,
                target_function="camera_rot_y",
                target_min=DialSettings.ROT_Y.min,
                target_max=DialSettings.ROT_Y.max,
                description="Y Rotation",
            ),
        )

        self.add_mapping(
            "rotation_z",
            MIDIMapping(
                control_number=4,
                channel=0,
                control_type=MIDIControlType.KNOB,
                target_function="camera_rot_z",
                target_min=DialSettings.ROT_Z.min,
                target_max=DialSettings.ROT_Z.max,
                description="Z Rotation",
            ),
        )

        # Translation controls
        self.add_mapping(
            "translate_x",
            MIDIMapping(
                control_number=5,
                channel=0,
                control_type=MIDIControlType.FADER,
                target_function="camera_trans_x",
                target_min=DialSettings.TRANSLATE_X.min,
                target_max=DialSettings.TRANSLATE_X.max,
                description="X Translation",
            ),
        )

        self.add_mapping(
            "translate_y",
            MIDIMapping(
                control_number=6,
                channel=0,
                control_type=MIDIControlType.FADER,
                target_function="camera_trans_y",
                target_min=DialSettings.TRANSLATE_Y.min,
                target_max=DialSettings.TRANSLATE_Y.max,
                description="Y Translation",
            ),
        )

        # Connolly surface controls
        self.add_mapping(
            "connolly_transparency",
            MIDIMapping(
                control_number=7,
                channel=0,
                control_type=MIDIControlType.KNOB,
                target_function="connolly_transparency",
                target_min=0.0,
                target_max=1.0,
                description="Connolly Surface Transparency",
            ),
        )

        self.add_mapping(
            "connolly_probe_radius",
            MIDIMapping(
                control_number=8,
                channel=0,
                control_type=MIDIControlType.KNOB,
                target_function="connolly_probe_radius",
                target_min=0.5,
                target_max=3.0,
                description="Connolly Probe Radius",
            ),
        )

        # Fog controls
        self.add_mapping(
            "fog_density",
            MIDIMapping(
                control_number=9,
                channel=0,
                control_type=MIDIControlType.KNOB,
                target_function="fog_density",
                target_min=DialSettings.FOG_DENSITY.min,
                target_max=DialSettings.FOG_DENSITY.max,
                description="Fog Density",
            ),
        )

        self.add_mapping(
            "fog_near",
            MIDIMapping(
                control_number=11,
                channel=0,
                control_type=MIDIControlType.KNOB,
                target_function="fog_near",
                target_min=DialSettings.FOG_NEAR.min,
                target_max=DialSettings.FOG_NEAR.max,
                description="Fog Near Distance",
            ),
        )

        self.add_mapping(
            "fog_far",
            MIDIMapping(
                control_number=12,
                channel=0,
                control_type=MIDIControlType.KNOB,
                target_function="fog_far",
                target_min=DialSettings.FOG_FAR.min,
                target_max=DialSettings.FOG_FAR.max,
                description="Fog Far Distance",
            ),
        )

        # Clipping controls
        self.add_mapping(
            "clip_z",
            MIDIMapping(
                control_number=13,
                channel=0,
                control_type=MIDIControlType.KNOB,
                target_function="clip_z",
                target_min=DialSettings.CLIP_Z.min,
                target_max=DialSettings.CLIP_Z.max,
                description="Clipping Z Position",
            ),
        )

        self.add_mapping(
            "clip_depth",
            MIDIMapping(
                control_number=14,
                channel=0,
                control_type=MIDIControlType.KNOB,
                target_function="clip_depth",
                target_min=DialSettings.CLIP_DEPTH.min,
                target_max=DialSettings.CLIP_DEPTH.max,
                description="Clipping Depth",
            ),
        )

        # Isosurface controls
        self.add_mapping(
            "isosurface_level",
            MIDIMapping(
                control_number=10,
                channel=0,
                control_type=MIDIControlType.KNOB,
                target_function="isosurface_level",
                target_min=0.01,
                target_max=1.0,
                description="Isosurface Level",
            ),
        )

    def add_mapping(self, name: str, mapping: MIDIMapping):
        """Add a MIDI control mapping"""
        self.mappings[name] = mapping
        log.debug(f"🎛️ Added MIDI mapping: {name} -> {mapping.target_function}")

    def remove_mapping(self, name: str):
        """Remove a MIDI control mapping"""
        if name in self.mappings:
            del self.mappings[name]
            log.debug(f"🎛️ Removed MIDI mapping: {name}")

    def set_control_handler(self, function_name: str, handler: Callable):
        """Set a handler function for a specific control"""
        self.control_handlers[function_name] = handler
        log.debug(f"🎛️ Set control handler: {function_name}")

    def list_available_ports(self) -> List[str]:
        """List available MIDI input ports"""
        if not MIDI_AVAILABLE:
            return []

        try:
            self.available_ports = mido.get_input_names()
            return self.available_ports
        except Exception as e:
            log.error(f"❌ Error listing MIDI ports: {e}")
            return []

    def connect_to_port(self, port_name: str) -> bool:
        """Connect to a specific MIDI input port"""
        if not MIDI_AVAILABLE:
            log.error("❌ MIDI not available")
            return False

        try:
            if self.midi_input:
                self.disconnect()

            self.midi_input = mido.open_input(port_name)
            self.current_port = port_name
            log.info(f"🎛️ Connected to MIDI port: {port_name}")
            return True
        except Exception as e:
            log.error(f"❌ Error connecting to MIDI port {port_name}: {e}")
            return False

    def disconnect(self):
        """Disconnect from MIDI input"""
        if self.midi_input:
            try:
                self.midi_input.close()
                self.midi_input = None
                self.current_port = None
                log.info("🎛️ Disconnected from MIDI")
            except Exception as e:
                log.error(f"❌ Error disconnecting from MIDI: {e}")

    def start_listening(self):
        """Start listening for MIDI messages"""
        if not self.midi_input:
            log.error("❌ No MIDI input connected")
            return False

        if self.is_running:
            log.warning("⚠️ MIDI controller already running")
            return False

        self.is_running = True
        self.midi_thread = threading.Thread(target=self._midi_loop, daemon=True)
        self.midi_thread.start()
        log.info("🎛️ Started MIDI listening")
        return True

    def stop_listening(self):
        """Stop listening for MIDI messages"""
        self.is_running = False
        if self.midi_thread:
            self.midi_thread.join(timeout=1.0)
        log.info("🎛️ Stopped MIDI listening")

    def _midi_loop(self):
        """Main MIDI listening loop"""
        try:
            for msg in self.midi_input:
                if not self.is_running:
                    break

                if msg.type == "control_change":
                    self._handle_control_change(msg)
                elif msg.type == "note_on":
                    self._handle_note_on(msg)
                elif msg.type == "note_off":
                    self._handle_note_off(msg)

        except Exception as e:
            log.error(f"❌ Error in MIDI loop: {e}")
        finally:
            self.is_running = False

    def _handle_control_change(self, msg):
        """Handle MIDI control change messages"""
        control_number = msg.control
        channel = msg.channel
        value = msg.value

        # Find matching mapping
        for name, mapping in self.mappings.items():
            if (
                mapping.control_number == control_number
                and mapping.channel == channel
                and mapping.enabled
            ):
                # Convert MIDI value to target range
                target_value = self._convert_midi_value(value, mapping)

                # Call the handler
                self._call_control_handler(mapping.target_function, target_value)

                log.debug(
                    f"🎛️ MIDI Control: {name} -> {mapping.target_function} = {target_value}"
                )
                break

    def _handle_note_on(self, msg):
        """Handle MIDI note on messages (for buttons)"""
        # Could be used for toggle controls
        pass

    def _handle_note_off(self, msg):
        """Handle MIDI note off messages"""
        # Could be used for momentary controls
        pass

    def _convert_midi_value(self, midi_value: int, mapping: MIDIMapping) -> float:
        """Convert MIDI value (0-127) to target range"""
        # Normalize MIDI value to 0-1
        normalized = midi_value / 127.0

        # Map to target range
        target_value = mapping.target_min + (
            normalized * (mapping.target_max - mapping.target_min)
        )

        return target_value

    def _call_control_handler(self, function_name: str, value: float):
        """Call the appropriate control handler with throttling"""
        if function_name not in self.control_handlers:
            log.debug(f"🎛️ No handler for control: {function_name}")
            return

        current_time = time.time()

        # Check if we should throttle this control
        if function_name in self._last_update_times:
            # Use special throttling interval for expensive controls
            throttle_interval = self._expensive_controls.get(
                function_name, self._throttle_interval
            )
            time_since_last = current_time - self._last_update_times[function_name]
            if time_since_last < throttle_interval:
                # Skip this update due to throttling
                log.debug(
                    f"🎛️ Throttling {function_name} (last update {time_since_last:.3f}s ago)"
                )
                return

        # Check if value has changed significantly (for float values)
        if function_name in self._last_values:
            last_value = self._last_values[function_name]
            value_change = abs(value - last_value)
            # Only update if change is significant (0.1% of range or 0.001 absolute)
            if value_change < max(0.001, abs(value) * 0.001):
                return

        try:
            self.control_handlers[function_name](value)
            self._last_update_times[function_name] = current_time
            self._last_values[function_name] = value
            log.debug(f"🎛️ MIDI Control: {function_name} = {value:.6f}")
        except Exception as e:
            log.error(f"❌ Error calling control handler {function_name}: {e}")

    def get_mapping_info(self) -> Dict[str, Dict]:
        """Get information about all current mappings"""
        info = {}
        for name, mapping in self.mappings.items():
            info[name] = {
                "control_number": mapping.control_number,
                "channel": mapping.channel,
                "control_type": mapping.control_type.value,
                "target_function": mapping.target_function,
                "target_range": (mapping.target_min, mapping.target_max),
                "enabled": mapping.enabled,
                "description": mapping.description,
            }
        return info

    def enable_mapping(self, name: str):
        """Enable a specific mapping"""
        if name in self.mappings:
            self.mappings[name].enabled = True
            log.debug(f"🎛️ Enabled mapping: {name}")

    def disable_mapping(self, name: str):
        """Disable a specific mapping"""
        if name in self.mappings:
            self.mappings[name].enabled = False
            log.debug(f"🎛️ Disabled mapping: {name}")

    def is_connected(self) -> bool:
        """Check if connected to MIDI input"""
        return self.midi_input is not None and self.current_port is not None

    def is_listening(self) -> bool:
        """Check if actively listening for MIDI messages"""
        return self.is_running

    def set_throttle_interval(self, control_name: str, interval: float):
        """Set custom throttle interval for a specific control"""
        self._expensive_controls[control_name] = interval
        log.debug(f"🎛️ Set throttle interval for {control_name}: {interval}s")

    def get_throttle_info(self) -> Dict[str, float]:
        """Get current throttle settings"""
        return {
            "default_interval": self._throttle_interval,
            "expensive_controls": self._expensive_controls.copy(),
        }

    def clear_throttle_state(self):
        """Clear throttle state (useful for testing or reset)"""
        self._last_update_times.clear()
        self._last_values.clear()
        log.debug("🎛️ Cleared throttle state")


def create_elmo_midi_controller(main_window) -> MIDIController:
    """Create a MIDI controller configured for ElMo"""
    controller = MIDIController(main_window)

    # Set up control handlers for ElMo
    if main_window and hasattr(main_window, "glmol"):
        glmol = main_window.glmol

        # Camera controls
        controller.set_control_handler("camera_zoom", glmol.set_zoom)
        controller.set_control_handler("camera_rot_x", glmol.set_rot_x)
        controller.set_control_handler("camera_rot_y", glmol.set_rot_y)
        controller.set_control_handler("camera_rot_z", glmol.set_rot_z)
        controller.set_control_handler("camera_trans_x", glmol.set_trans_x)
        controller.set_control_handler("camera_trans_y", glmol.set_trans_y)

        # Fog controls
        controller.set_control_handler("fog_density", glmol.set_fog_density)

        def set_fog_near(value):
            glmol.state.ui.camera.fog_near.value = value
            glmol.update()

        def set_fog_far(value):
            glmol.state.ui.camera.fog_far.value = value
            glmol.update()

        controller.set_control_handler("fog_near", set_fog_near)
        controller.set_control_handler("fog_far", set_fog_far)

        # Clipping controls
        def set_clip_z(value):
            glmol.state.ui.camera.clip_z.value = value
            glmol.update()

        def set_clip_depth(value):
            glmol.state.ui.camera.clip_depth.value = value
            glmol.update()

        controller.set_control_handler("clip_z", set_clip_z)
        controller.set_control_handler("clip_depth", set_clip_depth)

        # Isosurface controls
        def set_isosurface_level(value):
            glmol.state.ui.view.isosurface_sigma_level = value
            glmol.extract_isosurface()
            glmol.update()

        controller.set_control_handler("isosurface_level", set_isosurface_level)

        # Connolly surface controls (these need special handling)
        def set_connolly_transparency(value):
            if hasattr(main_window, "dynamic_model_tab_manager"):
                active_model_id = (
                    main_window.dynamic_model_tab_manager.get_active_model_id()
                )
                if active_model_id:
                    widget = (
                        main_window.dynamic_model_tab_manager.get_model_view_widget(
                            active_model_id
                        )
                    )
                    if widget and hasattr(widget, "transparency_spin"):
                        widget.transparency_spin.setValue(value)

        def set_connolly_probe_radius(value):
            if hasattr(main_window, "dynamic_model_tab_manager"):
                active_model_id = (
                    main_window.dynamic_model_tab_manager.get_active_model_id()
                )
                if active_model_id:
                    widget = (
                        main_window.dynamic_model_tab_manager.get_model_view_widget(
                            active_model_id
                        )
                    )
                    if widget and hasattr(widget, "probe_radius_spin"):
                        widget.probe_radius_spin.setValue(value)

        controller.set_control_handler(
            "connolly_transparency", set_connolly_transparency
        )
        controller.set_control_handler(
            "connolly_probe_radius", set_connolly_probe_radius
        )

    return controller
