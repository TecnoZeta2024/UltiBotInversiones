import json
from decimal import Decimal
from uuid import UUID
from datetime import datetime, date

class CustomJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle special data types like Decimal, UUID, and datetime.
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)  # Convert Decimal to string to preserve precision
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

def custom_dumps(data):
    """
    Custom json.dumps function that uses the CustomJSONEncoder.
    """
    return json.dumps(data, cls=CustomJSONEncoder)
