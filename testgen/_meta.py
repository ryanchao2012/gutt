def get_version():
    try:
        from ._version import __version__

        return __version__

    except Exception:
        pass
