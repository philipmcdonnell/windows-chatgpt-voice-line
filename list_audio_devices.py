"""List Windows audio devices visible to PortAudio."""

from __future__ import annotations

import sounddevice as sd


def main() -> None:
    print(f"PortAudio: {sd.get_portaudio_version()[1]}")
    print(f"Default input/output indices: {sd.default.device}")
    print()

    devices = sd.query_devices()
    if not devices:
        raise RuntimeError("No audio devices were reported by PortAudio.")

    for index, device in enumerate(devices):
        roles: list[str] = []
        if device["max_input_channels"] > 0:
            roles.append("input")
        if device["max_output_channels"] > 0:
            roles.append("output")
        role_text = ", ".join(roles) or "unavailable"
        marker = "*" if index in sd.default.device else " "
        print(
            f"{marker} {index:>2}: {device['name']} "
            f"[{role_text}; {device['default_samplerate']:.0f} Hz]"
        )


if __name__ == "__main__":
    main()
