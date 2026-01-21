from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_compress import Compress
from flask_cors import CORS

# Initialize extensions
# Note: db is initialized in models.py to avoid heavy refactor of models for now
jwt = JWTManager()
mail = Mail()
compress = Compress()

# Configure CORS - Allow Vercel frontend
cors = CORS(
    resources={r"/api/*": {
        "origins": [
            "http://localhost:4200",
            "https://elvestuario-r4.vercel.app",
            "https://*.vercel.app"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 3600
    }}
)

# Default limits, can be overridden per route
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    default_limits=["2000 per day", "500 per hour"]
)
