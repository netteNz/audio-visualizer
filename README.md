# Audio Visualizer

A real-time audio visualizer that displays waveforms and frequency spectrum analysis using Python.

## Features

- **Oscilloscope View**: Real-time waveform display
- **Spectrum Analyzer**: FFT-based frequency domain visualization
- **Cross-Platform**: Support for macOS and Windows
- **Live Audio Input**: Captures microphone input in real-time

## Requirements

- Python 3.8+
- soundcard
- numpy
- dearpygui

## Installation

1. Clone the repository:
```bash
git clone https://github.com/netteNz/audio-visualizer.git
cd audio-visualizer
```

2. Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

## Usage
Run the visualizer
```bash
python3 mac.py
```

The application will open a window displaying real-time audio waveform and frequency spectrum.

macOS Setup
For macOS, you may need to install BlackHole for audio routing.

License
MIT