class BaksysUtils:
    def loadOption(option, name, default = None):
        if not name in option:
            return default
        return option[name]