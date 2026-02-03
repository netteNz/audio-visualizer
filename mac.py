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

# --- GUI SETUP ---
dpg.create_context()
with dpg.window(tag="Primary Window"):
    dpg.add_text("Minimeters Clone - Proto 2")
    
    # PLOT 1: OSCILLOSCOPE
    with dpg.plot(label="Oscilloscope", height=200, width=-1):
        dpg.add_plot_legend()
        dpg.add_plot_axis(dpg.mvXAxis, label="Time", no_tick_labels=True)
        dpg.add_plot_axis(dpg.mvYAxis, label="Amplitude", tag="y_axis_wave")
        dpg.set_axis_limits("y_axis_wave", -1.0, 1.0)
        
        dpg.add_line_series(
            list(range(DISPLAY_LENGTH)), 
            list(audio_data), 
            label="Waveform", 
            parent="y_axis_wave", 
            tag="wave_series"
        )

    # PLOT 2: SPECTRUM ANALYZER
    with dpg.plot(label="Spectrum (FFT)", height=200, width=-1):
        dpg.add_plot_legend()
        
        # X-Axis: Frequency Bins
        dpg.add_plot_axis(dpg.mvXAxis, label="Frequency Bin", tag="x_axis_fft")
        
        # Y-Axis: Decibels
        dpg.add_plot_axis(dpg.mvYAxis, label="Decibels (dB)", tag="y_axis_fft")
        dpg.set_axis_limits("y_axis_fft", -100, 0) # Standard dB range
        
        dpg.add_line_series(
            list(range(len(fft_data))), 
            list(fft_data), 
            label="Spectrum", 
            parent="y_axis_fft", 
            tag="fft_series"
        )

dpg.create_viewport(title='Minimeters Clone', width=800, height=500)
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
    # We copy the numpy array to a list for DPG
    current_fft = fft_data.tolist()
    dpg.set_value("fft_series", [list(range(len(current_fft))), current_fft])
    
    dpg.render_dearpygui_frame()

stream_running = False
dpg.destroy_context()