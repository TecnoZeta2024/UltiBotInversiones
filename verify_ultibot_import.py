try:
    import ultibot_backend
    import os
    print(f"ultibot_backend path: {os.path.dirname(ultibot_backend.__file__)}")
except ImportError as e:
    print(f"Import failed: {e}")