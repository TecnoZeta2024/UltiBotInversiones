"""
Application Configuration for UltiBot UI
"""

API_BASE_URL = "http://localhost:8000" # Default API base URL
# In a real application, you might load this from environment variables or a config file.
# Example:
# import os
# API_BASE_URL = os.getenv("ULTIBOT_API_URL", "http://localhost:8000")

# Other UI related configurations can be added here.
REQUEST_TIMEOUT = 30.0 # Default timeout for API requests in seconds
