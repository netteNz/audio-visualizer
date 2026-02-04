import soundcard as sc
import numpy as np
import dearpygui.dearpygui as dpg
import threading
import collections
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for rendering to buffer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from PIL import Image
import io

# --- CONFIGURATION ---
SAMPLE_RATE = 44100 
BUFFER_SIZE = 2048
DISPLAY_LENGTH = 2048 

# Frequency range for logarithmic scale (Hz)
FREQ_MIN = 20
FREQ_MAX = 20000

# Plot dimensions - optimized to fit window exactly  
PLOT_WIDTH = 970
PLOT_HEIGHT = 200

# Noise gate threshold (dB) - signals below this are considered silence
NOISE_GATE_THRESHOLD = -80

# Waveform amplification for more reactivity
WAVEFORM_GAIN = 1.8

# Colors - Professional audio tool palette
GREEN_WAVE = '#00FF7F'      # Waveform - classic oscilloscope green
AMBER_SPECTRUM = '#FF8C00'  # Spectrum - warm amber like DAWs
BG_COLOR = '#0a0a0e'        # Darker background
GRID_COLOR = '#1a1a22'      # Subtle grid

# --- SHARED DATA ---
audio_data = collections.deque([0.0] * DISPLAY_LENGTH, maxlen=DISPLAY_LENGTH)
fft_data = np.zeros(BUFFER_SIZE // 2 + 1)
stream_running = True

def audio_thread_func():
    global fft_data
    
    try:
        default_speaker = sc.default_speaker()
        print(f"Default speaker: {default_speaker.name}")
        
        mics = sc.all_microphones(include_loopback=True)
        
        loopback = None
        for mic in mics:
            if mic.isloopback:
                if default_speaker.name in mic.name or mic.name in default_speaker.name:
                    loopback = mic
                    break
        
        if loopback is None:
            for mic in mics:
                if mic.isloopback:
                    loopback = mic
                    break
        
        if loopback is None:
            print("No loopback device found.")
            return
            
        print(f"Audio Thread: Listening to loopback from '{loopback.name}'")
    except Exception as e:
        print(f"Error accessing loopback audio: {e}")
        return

    with loopback.recorder(samplerate=SAMPLE_RATE) as recorder:
        while stream_running:
            raw_buffer = recorder.record(numframes=BUFFER_SIZE)
            
            if raw_buffer.shape[0] > 0:
                if raw_buffer.shape[1] > 1:
                    mono_signal = np.mean(raw_buffer, axis=1)
                else:
                    mono_signal = raw_buffer[:, 0]

                audio_data.extend((mono_signal * WAVEFORM_GAIN).tolist())

                windowed = mono_signal * np.hanning(len(mono_signal))
                spectrum = np.abs(np.fft.rfft(windowed))
                spectrum_db = 20 * np.log10(spectrum + 1e-10)
                spectrum_db -= np.max(spectrum_db)
                
                # Apply noise gate - if signal is too quiet, show flat line at floor
                signal_level = np.max(np.abs(mono_signal))
                if signal_level < 0.001:  # Very quiet input
                    spectrum_db = np.full_like(spectrum_db, -100)
                
                fft_data = spectrum_db

def create_matplotlib_figures():
    """Create styled matplotlib figures for waveform and spectrum"""
    # Create figure for waveform
    fig_wave = plt.figure(figsize=(PLOT_WIDTH/100, PLOT_HEIGHT/100), dpi=100)
    fig_wave.patch.set_facecolor(BG_COLOR)
    ax_wave = fig_wave.add_subplot(111)
    ax_wave.set_facecolor(BG_COLOR)
    ax_wave.set_title('Waveform - Time Domain', color='white', fontsize=12, pad=10)
    ax_wave.set_ylabel('Amplitude', color='white', fontsize=9)
    ax_wave.set_ylim(-1.0, 1.0)
    ax_wave.set_xlim(0, DISPLAY_LENGTH)
    ax_wave.tick_params(colors='#808080', labelsize=8)
    ax_wave.grid(True, color=GRID_COLOR, alpha=0.5, linewidth=0.5)
    for spine in ax_wave.spines.values():
        spine.set_color(GRID_COLOR)
    line_wave, = ax_wave.plot([], [], color=GREEN_WAVE, linewidth=1.2)
    fig_wave.tight_layout(pad=0.5)
    
    # Create figure for spectrum with log scale
    fig_fft = plt.figure(figsize=(PLOT_WIDTH/100, PLOT_HEIGHT/100), dpi=100)
    fig_fft.patch.set_facecolor(BG_COLOR)
    ax_fft = fig_fft.add_subplot(111)
    ax_fft.set_facecolor(BG_COLOR)
    ax_fft.set_title('Spectrum - Frequency Domain (FFT)', color='white', fontsize=12, pad=10)
    ax_fft.set_ylabel('Magnitude (dB)', color='white', fontsize=9)
    ax_fft.set_ylim(-100, 0)
    ax_fft.set_xscale('log')
    ax_fft.set_xlim(FREQ_MIN, FREQ_MAX)
    ax_fft.set_xlabel('Frequency (Hz)', color='#666666', fontsize=8)
    ax_fft.tick_params(colors='#808080', labelsize=8)
    ax_fft.grid(True, color=GRID_COLOR, alpha=0.5, linewidth=0.5, which='both')
    for spine in ax_fft.spines.values():
        spine.set_color(GRID_COLOR)
    # Create line and fill for glassy effect
    line_fft, = ax_fft.plot([], [], color=AMBER_SPECTRUM, linewidth=1.0, alpha=0.9)
    fill_fft = None  # Will be created dynamically
    fig_fft.tight_layout(pad=0.5)
    
    return fig_wave, ax_wave, line_wave, fig_fft, ax_fft, line_fft

def fig_to_rgba(fig):
    """Convert matplotlib figure to RGBA numpy array"""
    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    
    # Get the RGBA buffer
    buf = np.asarray(canvas.buffer_rgba())
    return buf

def rgba_to_dpg_texture(rgba_array):
    """Convert RGBA array to DearPyGUI compatible format (flattened, normalized)"""
    # Normalize to 0-1 range and flatten
    return (rgba_array.astype(np.float32) / 255.0).flatten()

# --- GUI SETUP ---
dpg.create_context()

# Create matplotlib figures
fig_wave, ax_wave, line_wave, fig_fft, ax_fft, line_fft = create_matplotlib_figures()

# Initial render to get dimensions
initial_wave = fig_to_rgba(fig_wave)
initial_fft = fig_to_rgba(fig_fft)

# Create texture registry
with dpg.texture_registry(show=False):
    dpg.add_dynamic_texture(
        width=initial_wave.shape[1],
        height=initial_wave.shape[0],
        default_value=rgba_to_dpg_texture(initial_wave),
        tag="wave_texture"
    )
    dpg.add_dynamic_texture(
        width=initial_fft.shape[1],
        height=initial_fft.shape[0],
        default_value=rgba_to_dpg_texture(initial_fft),
        tag="fft_texture"
    )

# Create global theme for dark background
with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (20, 20, 24, 255))
        dpg.add_theme_color(dpg.mvThemeCol_Text, (220, 220, 220, 255))
dpg.bind_theme(global_theme)

with dpg.window(tag="Primary Window"):
    # Title section
    dpg.add_text("AUDIO VISUALIZER", color=(0, 217, 255, 255))
    dpg.add_text("Desktop Audio Analysis", color=(150, 150, 150, 255))
    dpg.add_spacer(height=10)
    
    # Waveform plot (matplotlib rendered as texture)
    dpg.add_image("wave_texture")
    
    dpg.add_spacer(height=5)
    
    # Spectrum plot (matplotlib rendered as texture)
    dpg.add_image("fft_texture")

dpg.create_viewport(title='Audio Visualizer', width=1000, height=510)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)

# --- START THREAD ---
thread = threading.Thread(target=audio_thread_func, daemon=True)
thread.start()

# Pre-compute frequency array for log scale
freq_hz = np.fft.rfftfreq(BUFFER_SIZE, 1/SAMPLE_RATE)
valid_mask = (freq_hz >= FREQ_MIN) & (freq_hz <= FREQ_MAX)
freq_valid = freq_hz[valid_mask]

# --- RENDER LOOP ---
frame_skip = 0
while dpg.is_dearpygui_running():
    frame_skip += 1
    
    # Update matplotlib plots every 3 frames for performance
    if frame_skip >= 3:
        frame_skip = 0
        
        # Update waveform
        wave_data = list(audio_data)
        line_wave.set_data(range(len(wave_data)), wave_data)
        wave_rgba = fig_to_rgba(fig_wave)
        dpg.set_value("wave_texture", rgba_to_dpg_texture(wave_rgba))
        
        # Update spectrum with log frequency scale
        fft_data_array = np.array(fft_data)
        fft_valid = fft_data_array[:len(freq_hz)][valid_mask]
        
        # Smooth the FFT data for cleaner peaks (5-point moving average)
        kernel = np.ones(5) / 5
        fft_smoothed = np.convolve(fft_valid, kernel, mode='same')
        
        # Update line
        line_fft.set_data(freq_valid, fft_smoothed)
        
        # Clear old fill and add single glassy fill (faster)
        for collection in ax_fft.collections:
            collection.remove()
        ax_fft.fill_between(freq_valid, -100, fft_smoothed, 
                           color=AMBER_SPECTRUM, alpha=0.3)
        
        fft_rgba = fig_to_rgba(fig_fft)
        dpg.set_value("fft_texture", rgba_to_dpg_texture(fft_rgba))
    
    dpg.render_dearpygui_frame()

stream_running = False
plt.close('all')
dpg.destroy_context()
