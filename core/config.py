from pathlib import Path


class ConfigManager:
    def __init__(self):
        self.values = {}
        config = Path.home() / "ai-server" / "config" / "server.conf"
        if not config.exists():
            return
        for line in config.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            self.values[key.strip()] = value.strip().strip('"')

    def get(self, key, default=None):
        return self.values.get(key, default)
