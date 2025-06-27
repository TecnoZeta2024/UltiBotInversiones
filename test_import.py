try:
    from ultibot_backend.api.v1.services.opportunities import OpportunitiesService
    print("Import successful!")
except ImportError as e:
    print(f"Import failed: {e}")