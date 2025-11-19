import sounddevice as sd
import wave
import numpy as np
import threading
import time

# Audio recording parameters
SAMPLE_RATE = 16000
CHANNELS = 1
OUTPUT_FILENAME = "recording2.wav"

# Global variables
recording = []
stop_recording = threading.Event()

def list_audio_devices():
    """List all available audio devices with index numbers"""
    print("\n=== Available Audio Input Devices ===")
    devices = sd.query_devices()
    input_devices = []
    
    for idx, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            input_devices.append(idx)
            print(f"[{idx}] {device['name']}")
            print(f"    Channels: {device['max_input_channels']}, Sample Rate: {device['default_samplerate']}")
    
    return input_devices

def test_microphone(device_id=None):
    """Test if microphone is working"""
    print("\nTesting microphone for 3 seconds...")
    test_data = []
    
    try:
        with sd.InputStream(
            device=device_id,
            samplerate=SAMPLE_RATE, 
            channels=CHANNELS, 
            dtype='int16',
            blocksize=1024
        ) as stream:
            for _ in range(int(3 * SAMPLE_RATE / 1024)):
                data, overflowed = stream.read(1024)
                test_data.append(data.copy())
        
        audio_array = np.concatenate(test_data, axis=0)
        max_amp = np.max(np.abs(audio_array))
        mean_amp = np.mean(np.abs(audio_array))
        
        print(f"Max amplitude: {max_amp}")
        print(f"Mean amplitude: {mean_amp}")
        
        if max_amp > 100:
            print("✓ Microphone is working!")
            return True
        else:
            print("✗ No sound detected from this device")
            return False
            
    except Exception as e:
        print(f"✗ Error testing device: {e}")
        return False

def record_audio(device_id=None):
    """Record audio from microphone"""
    print("\nRecording... Press Enter to stop.")
    try:
        with sd.InputStream(
            device=device_id,
            samplerate=SAMPLE_RATE, 
            channels=CHANNELS, 
            dtype='int16',
            blocksize=1024
        ) as stream:
            while not stop_recording.is_set():
                data, overflowed = stream.read(1024)
                if overflowed:
                    print("!", end="", flush=True)
                recording.append(data.copy())
    except Exception as e:
        print(f"\nError during recording: {e}")
    
    print("\nStopping recording...")

# Main program
if __name__ == "__main__":
    # List all input devices
    input_devices = list_audio_devices()
    
    if not input_devices:
        print("\n✗ No input devices found!")
        exit(1)
    
    # Ask user to select device
    print("\n" + "="*50)
    device_choice = input("Enter device number to use (or press Enter for default): ").strip()
    
    if device_choice == "":
        device_id = None
        print("Using default input device")
    else:
        try:
            device_id = int(device_choice)
            if device_id not in input_devices:
                print(f"Invalid device number. Using default.")
                device_id = None
            else:
                print(f"Using device [{device_id}]")
        except ValueError:
            print("Invalid input. Using default device.")
            device_id = None
    
    # Test the microphone
    print("\n" + "="*50)
    test_choice = input("Test microphone first? (y/n): ").strip().lower()
    
    if test_choice == 'y':
        if not test_microphone(device_id):
            retry = input("\nMicrophone test failed. Continue anyway? (y/n): ").strip().lower()
            if retry != 'y':
                print("Exiting...")
                exit(0)
    
    # Start recording
    print("\n" + "="*50)
    input("Press ENTER to start recording...")
    
    record_thread = threading.Thread(target=record_audio, args=(device_id,))
    record_thread.start()
    
    # Wait for Enter key to stop
    input()
    
    # Stop recording
    stop_recording.set()
    record_thread.join()
    
    # Save the recording
    if recording:
        audio_data = np.concatenate(recording, axis=0)
        
        # Check audio levels
        max_amplitude = np.max(np.abs(audio_data))
        mean_amplitude = np.mean(np.abs(audio_data))
        
        print(f"\nAudio Statistics:")
        print(f"  Max amplitude: {max_amplitude}")
        print(f"  Mean amplitude: {mean_amplitude}")
        
        if max_amplitude < 100:
            print("\n⚠ WARNING: Very low audio levels detected!")
        
        # Write WAV file
        with wave.open(OUTPUT_FILENAME, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_data.tobytes())
        
        import os
        full_path = os.path.abspath(OUTPUT_FILENAME)
        duration = len(audio_data) / SAMPLE_RATE
        
        print(f"\n✓ Recording saved!")
        print(f"  Location: {full_path}")
        print(f"  Duration: {duration:.2f} seconds")
        print(f"  Sample Rate: {SAMPLE_RATE} Hz")
    else:
        print("\n✗ No audio recorded.")