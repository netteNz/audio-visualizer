import platform
import sys

# Detect OS
CURRENT_OS = platform.system()  # Returns 'Windows' or 'Darwin' (macOS)

def main():
    """Launch platform-specific audio visualizer"""
    print(f"Detected OS: {CURRENT_OS}")
    
    if CURRENT_OS == 'Windows':
        print("Starting Windows audio visualizer (Loopback mode)...")
        import windows
    elif CURRENT_OS == 'Darwin':
        print("Starting macOS audio visualizer...")
        import mac
    else:
        print(f"Unsupported OS: {CURRENT_OS}")
        print("This application supports Windows and macOS only.")
        sys.exit(1)

if __name__ == "__main__":
    main()