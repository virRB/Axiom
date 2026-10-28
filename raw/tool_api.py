class API:
    def __init__(self: API, **args) -> None:
        for key, val in args.items():
            if hasattr(self, key):
                continue
            setattr(self, key, val)