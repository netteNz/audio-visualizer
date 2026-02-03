import platform

# Detect OS
CURRENT_OS = platform.system() # Returns 'Windows' or 'Darwin' (macOS)

def get_input_device():
    if CURRENT_OS == 'Windows':
        # Auto-find Windows Loopback
        return sc.default_speaker().name 
    elif CURRENT_OS == 'Darwin':
        # Hardcode BlackHole for Mac dev
        return "BlackHole 2ch"