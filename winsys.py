import ctypes

def is_admin() -> bool:
    return ctypes.windll.shell32.IsUserAnAdmin()