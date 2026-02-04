# Audio Visualizer

A real-time audio visualizer that displays waveforms and frequency spectrum analysis using Python.

## Features

- **Oscilloscope View**: Real-time waveform display
- **Spectrum Analyzer**: FFT-based frequency domain visualization
- **Cross-Platform**: Support for macOS and Windows
- **Live Audio Input**: Captures audio in real-time
  - **macOS**: Captures microphone input (or BlackHole for loopback)
  - **Windows**: Captures desktop audio via WASAPI loopback

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

2. Create and activate a virtual environment:

**Windows:**
```bash
python -m venv audio
audio\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the visualizer:
```bash
python main.py
```

The application will automatically detect your OS and:
- **Windows**: Visualize desktop audio (what's playing on your computer)
- **macOS**: Visualize microphone input (or BlackHole if configured)

The application window displays:
- **Oscilloscope**: Real-time waveform (time domain)
- **Spectrum Analyzer**: Frequency spectrum with FFT analysis (frequency domain)

## Platform-Specific Notes

### Windows
The visualizer uses WASAPI loopback to capture desktop audio from your default audio device. Just play some music or audio and watch the visualization respond!

### macOS
For capturing desktop audio on macOS, you may need to install [BlackHole](https://github.com/ExistentialAudio/BlackHole) for audio routing.

## License
MIT
