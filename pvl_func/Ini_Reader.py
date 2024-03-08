from configparser import ConfigParser

class IniReader:
    def __init__(self, file_path=None):
        self.file_path = file_path
        self.config = ConfigParser()
        self.config.read(file_path)

    def get_string(self, section, key, default_value):
        return self.config.get(section, key, fallback=default_value)

    def get_int(self, section, key, default_value):
        return self.config.getint(section, key, fallback=default_value)