import sounddevice as sd
import wave
import numpy as np
import sys
import threading

stop_flag = threading.Event()

def list_devices():
    print("\n=== AUDIO DEVICES ===\n")
    devices = sd.query_devices()
    for idx, d in enumerate(devices):
        print(f"[{idx}] {d['name']}   (inputs={d['max_input_channels']}, outputs={d['max_output_channels']})")
    return devices


def get_device_info(device_id):
    if device_id is None:
        return sd.query_devices(kind="input")
    else:
        return sd.query_devices(device_id)


def record_loop(device_id, sample_rate, frames_buffer):
    """Thread function that records audio in chunks until stop_flag is set."""
    with sd.InputStream(
        device=device_id,
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
        blocksize=2048
    ) as stream:
        while not stop_flag.is_set():
            data, overflow = stream.read(2048)
            frames_buffer.append(data.copy())


def record_audio(device_id=None, filename="recording.wav"):
    device_info = get_device_info(device_id)
    sample_rate = int(device_info["default_samplerate"])

    print(f"\n🎤 Using device: {device_info['name']}")
    print(f"🎵 Sample rate: {sample_rate} Hz")
    print("\nPress ENTER to start recording...")
    input()

    print("🔴 Recording... Press ENTER to stop.")

    frames = []
    stop_flag.clear()

    # Start thread
    t = threading.Thread(target=record_loop, args=(device_id, sample_rate, frames))
    t.start()

    input()  # Wait for second ENTER
    stop_flag.set()
    t.join()

    print("⏹ Stopped.")

    if len(frames) == 0:
        print("⚠ No audio captured!")
        return

    audio = np.concatenate(frames, axis=0)
    audio_int16 = (audio * 32767).astype(np.int16)

    # SAVE WAV
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())

    print(f"\n✅ Saved recording: {filename}")
    print(f"⏱ Duration: {len(audio) / sample_rate:.2f} seconds")

    # Playback
    if input("\n🔊 Play it? (y/n): ").strip().lower() == "y":
        sd.play(audio_int16, sample_rate)
        sd.wait()
        print("Done!")


# MAIN
# if __name__ == "__main__":
list_devices()
choice = input("\nEnter device index (ENTER for default): ").strip()
device_id = int(choice) if choice else None

record_audio(device_id, filename="recording.wav")
