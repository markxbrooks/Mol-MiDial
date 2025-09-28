# MolMiDial 🎛️🧬

**MolMiDial** is an open-source bridge between **MIDI controllers** and **molecular visualization tools** (PyMOL, Coot, ElMo, and more). Turn dials, push faders, and rotate knobs to control camera angles, isosurface levels, clipping planes, and other visualization parameters — in real time.

## ✨ Features
- 🎚️ **MIDI Mapping**: Map knobs, sliders, and buttons to molecular visualization functions.
- 🔄 **Live Updates**: Smooth, throttled updates for fast camera moves and surface manipulation.
- 🧠 **Extensible**: Add support for new software or control protocols (OSC, game controllers) easily.
- 🖥️ **Cross-Platform**: Runs on macOS, Linux, Windows.

## 🚀 Quick Start
```bash
# Clone the repository
git clone https://github.com/markxbrooks/MolMiDial.git
cd MolMiDial

# (Optional) create and activate a virtualenv
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -e .

# Launch demo
python -m molmidial.demo
```

## 🎛 Example Use Case
- Control **PyMOL** camera zoom and rotation with a MIDI knob bank
- Adjust **Connolly surface transparency** and probe radius interactively
- Scrub through **isosurface levels** like EQ frequencies on a synth
- Trigger **visualization presets** with MIDI buttons

## 📂 Project Layout
```
MolMiDial/
├── molmidial/          # Core Python package
│   ├── __init__.py
│   ├── controller.py   # Main MIDI controller class
│   ├── mappings.py     # Default MIDI mappings
│   └── integrations/   # PyMOL, Coot, ElMo bridges
├── examples/           # Example mapping configs & demos
├── tests/              # Unit tests
├── README.md
├── LICENSE
├── pyproject.toml
└── .gitignore
```

## 🛠 Development
```bash
# Install dev dependencies
pip install -e .[dev]

# Run tests
pytest -v
```

## 🤝 Contributing
Pull requests welcome! Please open an issue first to discuss major changes.

See [CONTRIBUTING.md](CONTRIBUTING.md) for coding style and guidelines.

## 📜 License
[MIT License](LICENSE)

---

### 💡 Logo Idea
A **protein ribbon cartoon** forming a circle, with a **MIDI knob** in the center — symbolizing molecule + dial. Optional musical note motif for flair.
