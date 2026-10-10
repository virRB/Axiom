class API:
    def __init__(self: API,
                cwd: str
                ) -> None:
        for key, val in locals().items():
            if key != "self":
                setattr(self, key, val)