from __future__ import annotations

import json
import socket
from pathlib import Path

from mcp_server.config import load_settings


def port_open(host, port):
    s = socket.socket()
    s.settimeout(2)
    try:
        s.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def main():
    settings = load_settings()
    report = {
        "config_host": settings.host,
        "config_port": settings.port,
        "security_mode": settings.security.mode,
        "bridge_port_open": port_open(settings.host, settings.port),
        "plugin_present": (
            Path(__file__).resolve().parents[1] / "UnrealEngineMCP" / "UnrealEngineMCP.uplugin"
        ).is_file(),
    }
    print(json.dumps(report, indent=2))
    if not report["bridge_port_open"]:
        print("Hint: start Unreal Editor with UnrealEngineMCP plugin enabled.")


if __name__ == "__main__":
    main()
