from configparser import ConfigParser


class TecCommSetting:
    def __init__(self, file_path):
        self.config = ConfigParser()
        self.config.read(file_path)

        self.port = self.config.get('Settings', 'Port', fallback='Unknown')
        self.baudrate = self.config.getint('Settings', 'Baudrate', fallback=0)
        self.data_bits = self.config.getint('Settings', 'DataBits', fallback=8)
        self.parity = self.config.getint('Settings', 'Parity', fallback=0)
        self.stop_bits = self.config.getint('Settings', 'StopBits', fallback=0)