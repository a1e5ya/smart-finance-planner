# app/routers/__init__.py

# Import all routers for easy access
from . import auth
from . import chat

# Import separated transaction routers
from . import transactions_router
from . import transaction_import_router  
from . import transaction_analytics_router

# Make routers available for import
__all__ = [
    "auth",
    "chat", 
    "transactions_router",
    "transaction_import_router",
    "transaction_analytics_router"
]