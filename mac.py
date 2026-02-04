import soundcard as sc
import numpy as np
import dearpygui.dearpygui as dpg
import threading
import collections

# --- CONFIGURATION ---
SAMPLE_RATE = 44100 
BUFFER_SIZE = 2048 # Increased for better bass resolution (Frequency Resolution = SampleRate / BufferSize)
DISPLAY_LENGTH = 2048 

# --- SHARED DATA ---
# We now need TWO queues: one for the wave, one for the spectrum
audio_data = collections.deque([0.0] * DISPLAY_LENGTH, maxlen=DISPLAY_LENGTH)
fft_data = np.zeros(BUFFER_SIZE // 2 + 1) # FFT returns half the buffer size (Nyquist)
stream_running = True

def amplitude_to_color(amplitude_db):
    """Convert amplitude in dB to a spectrogram color (blue -> cyan -> green -> yellow -> red)"""
    # Normalize dB range (-100 to 0) to (0 to 1)
    normalized = np.clip((amplitude_db + 100) / 100, 0, 1)
    
    # Create color gradient (spectrogram-like)
    if normalized < 0.25:
        # Dark blue to cyan
        t = normalized / 0.25
        r, g, b = int(0 * (1-t) + 0 * t), int(50 * (1-t) + 150 * t), int(100 * (1-t) + 255 * t)
    elif normalized < 0.5:
        # Cyan to green
        t = (normalized - 0.25) / 0.25
        r, g, b = int(0 * (1-t) + 50 * t), int(150 * (1-t) + 255 * t), int(255 * (1-t) + 100 * t)
    elif normalized < 0.75:
        # Green to yellow
        t = (normalized - 0.5) / 0.25
        r, g, b = int(50 * (1-t) + 255 * t), int(255), int(100 * (1-t) + 0 * t)
    else:
        # Yellow to red
        t = (normalized - 0.75) / 0.25
        r, g, b = int(255), int(255 * (1-t) + 100 * t), int(0)
    
    return (r, g, b, 255)

def audio_thread_func():
    global fft_data
    
    # Auto-detect default mic
    try:
        mic = sc.default_microphone()
        print(f"Audio Thread: Listening to '{mic.name}'")
    except:
        return

    with mic.recorder(samplerate=SAMPLE_RATE) as recorder:
        while stream_running:
            # 1. Capture Data
            raw_buffer = recorder.record(numframes=BUFFER_SIZE)
            
            if raw_buffer.shape[0] > 0:
                # Handle Mono/Stereo
                if raw_buffer.shape[1] > 1:
                    mono_signal = np.mean(raw_buffer, axis=1)
                else:
                    mono_signal = raw_buffer[:, 0]

                # 2. Update Waveform Data (Time Domain)
                audio_data.extend(mono_signal.tolist())

                # 3. COMPUTE FFT (Frequency Domain)
                # Apply Hanning Window to smooth edges
                windowed = mono_signal * np.hanning(len(mono_signal))
                
                # Calculate FFT (rfft is for real-valued inputs like audio)
                spectrum = np.abs(np.fft.rfft(windowed))
                
                # Convert to Decibels (dB)
                # We add a tiny epsilon (1e-10) to avoid log(0) errors
                spectrum_db = 20 * np.log10(spectrum + 1e-10)
                
                # Normalize reference (rough calibration)
                spectrum_db -= np.max(spectrum_db) 
                
                # Update the shared variable
                fft_data = spectrum_db

# --- SETUP CUSTOM THEME ---
def setup_theme():
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            # Background colors
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (20, 20, 28, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (25, 25, 35, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (30, 30, 40, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (40, 40, 50, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (50, 50, 60, 255))
            
            # Text
            dpg.add_theme_color(dpg.mvThemeCol_Text, (220, 220, 220, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (128, 128, 128, 255))
            
            # Borders and lines
            dpg.add_theme_color(dpg.mvThemeCol_Border, (60, 60, 70, 128))
            dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (0, 0, 0, 0))
            
            # Title bar
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (15, 15, 20, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (20, 20, 30, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgCollapsed, (15, 15, 20, 255))
            
            # Plot backgrounds (but NOT line colors - those are set per-series)
            dpg.add_theme_color(dpg.mvPlotCol_FrameBg, (25, 25, 35, 255))
            dpg.add_theme_color(dpg.mvPlotCol_PlotBg, (18, 18, 25, 255))
            
            # Spacing and rounding
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 8)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 15, 15)
    
    dpg.bind_theme(global_theme)

# --- GUI SETUP ---
dpg.create_context()

with dpg.window(tag="Primary Window"):
    # Title section
    dpg.add_text("AUDIO VISUALIZER", color=(0, 217, 255, 255))
    dpg.add_text("Microphone Input Analysis", color=(150, 150, 150, 255))
    dpg.add_spacer(height=10)
    
    # PLOT 1: OSCILLOSCOPE
    with dpg.plot(label="Waveform - Time Domain", height=280, width=-1):
        dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
        x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="", no_tick_labels=True)
        y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Amplitude", tag="y_axis_wave")
        dpg.set_axis_limits("y_axis_wave", -1.0, 1.0)
        
        # Cyan waveform line
        dpg.add_line_series(
            list(range(DISPLAY_LENGTH)), 
            list(audio_data), 
            label="Signal", 
            parent="y_axis_wave", 
            tag="wave_series"
        )
    
    dpg.add_spacer(height=5)
    
    # PLOT 2: SPECTRUM ANALYZER (with spectrogram colors)
    with dpg.plot(label="Spectrum - Frequency Domain (FFT)", height=280, width=-1):
        dpg.add_plot_legend(location=dpg.mvPlot_Location_NorthEast)
        dpg.add_plot_axis(dpg.mvXAxis, label="Frequency Bin", no_tick_labels=True, tag="x_axis_fft")
        dpg.add_plot_axis(dpg.mvYAxis, label="Magnitude (dB)\", tag="y_axis_fft")
        dpg.set_axis_limits("y_axis_fft", -100, 0)
        
        # Use line series with vibrant purple for spectrogram-inspired look
        dpg.add_line_series(
            list(range(len(fft_data))), 
            list(fft_data),
            label="Spectrum",
            parent="y_axis_fft",
            tag="fft_series\"
        )

# Create themes for custom line colors
# Waveform theme - CYAN
wave_theme = dpg.add_theme()
with dpg.theme_component(dpg.mvLineSeries, parent=wave_theme):
    dpg.add_theme_color(dpg.mvPlotCol_Line, (0, 217, 255, 255))
    dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 2.0)

dpg.bind_item_theme("wave_series", wave_theme)

# FFT theme - PURPLE  
fft_theme = dpg.add_theme()
with dpg.theme_component(dpg.mvLineSeries, parent=fft_theme):
    dpg.add_theme_color(dpg.mvPlotCol_Line, (200, 60, 255, 255))
    dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 2.5)

dpg.bind_item_theme("fft_series", fft_theme)

# Apply the global theme AFTER series themes are bound
setup_theme()

dpg.create_viewport(title='Audio Visualizer', width=1000, height=660)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)

# --- START THREAD ---
thread = threading.Thread(target=audio_thread_func, daemon=True)
thread.start()

# --- RENDER LOOP ---
while dpg.is_dearpygui_running():
    # Update Waveform
    dpg.set_value("wave_series", [list(range(len(audio_data))), list(audio_data)])
    
    # Update FFT
    current_fft = fft_data.tolist()
    dpg.set_value("fft_series", [list(range(len(current_fft))), current_fft])
    
    dpg.render_dearpygui_frame()

stream_running = False
dpg.destroy_context()
