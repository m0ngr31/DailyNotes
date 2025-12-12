from quart import Quart
from quart_cors import cors
from config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps


app = Quart(
    __name__,
    static_url_path="/static",
    static_folder="../dist/static",
    template_folder="../dist",
)

app.config.from_object(Config)

# Enable CORS for development
# Note: Can't use wildcard "*" with credentials in quart-cors
# For development, allow localhost origins
app = cors(
    app,
    allow_origin=[
        "http://localhost:8080",
        "http://localhost:8000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
)

# Setup SQLAlchemy directly (pure SQLAlchemy without Flask-SQLAlchemy)
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
db_session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


class DatabaseWrapper:
    """Wrapper providing Flask-SQLAlchemy-like interface for Quart"""

    def __init__(self, engine, session, base):
        self.engine = engine
        self.session = session
        self.Model = base
        self.metadata = base.metadata

    def create_all(self):
        self.metadata.create_all(self.engine)


db = DatabaseWrapper(engine, db_session, Base)


# Session cleanup after each request
@app.teardown_appcontext
def shutdown_session(exception=None):
    """Remove the database session at the end of each request."""
    db_session.remove()


# Argon2 password hasher
password_hasher = PasswordHasher()


class Argon2Wrapper:
    """Wrapper providing flask-argon2 compatible interface using argon2-cffi for Quart"""

    def __init__(self, hasher):
        self._hasher = hasher

    def generate_password_hash(self, password):
        return self._hasher.hash(password)

    def check_password_hash(self, hash, password):
        try:
            self._hasher.verify(hash, password)
            return True
        except (VerifyMismatchError, InvalidHashError):
            return False


argon2 = Argon2Wrapper(password_hasher)


class JWTManager:
    """Custom JWT manager for Quart using PyJWT"""

    def __init__(self, app=None):
        self.secret_key = None
        self.algorithm = "HS256"
        self.token_expires = timedelta(days=7)
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.secret_key = app.config.get("JWT_SECRET_KEY")
        if not self.secret_key:
            raise ValueError("JWT_SECRET_KEY must be set in app configuration")
        expires = app.config.get("JWT_ACCESS_TOKEN_EXPIRES")
        if expires:
            self.token_expires = expires

    def create_access_token(self, identity):
        payload = {
            "sub": identity,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + self.token_expires,
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


jwt_manager = JWTManager(app)


def create_access_token(identity):
    """Create a JWT access token"""
    return jwt_manager.create_access_token(identity)


def get_jwt_identity():
    """Get the identity from the current request's JWT token"""
    from quart import request, g

    return getattr(g, "jwt_identity", None)


def jwt_required():
    """Decorator to require JWT authentication for a route"""

    def decorator(f):
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            from quart import request, g, abort

            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                abort(401)

            token = auth_header[7:]  # Remove "Bearer " prefix
            payload = jwt_manager.decode_token(token)

            if not payload:
                abort(401)

            g.jwt_identity = payload.get("sub")
            return await f(*args, **kwargs)

        return decorated_function

    return decorator


def verify_jwt_in_request():
    """Verify JWT token in current request (for manual verification)"""
    from quart import request, g, abort

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise Exception("Missing or invalid Authorization header")

    token = auth_header[7:]
    payload = jwt_manager.decode_token(token)

    if not payload:
        raise Exception("Invalid or expired token")

    g.jwt_identity = payload.get("sub")
    return payload


from app import routes, models
