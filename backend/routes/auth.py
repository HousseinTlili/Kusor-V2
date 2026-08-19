"""Auth namespace: login, current user."""
import bcrypt
from flask import request
from flask_restx import Namespace, Resource, fields, abort
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from backend.extensions import db
from backend.models.user import User

api = Namespace("auth", description="Authentication operations")

# RESTX Models for Swagger documentation
user_model = api.model("UserResponse", {
    "id": fields.String(description="User UUID"),
    "username": fields.String(description="User unique username"),
    "role": fields.String(description="User role (admin/user)"),
})

register_request = api.model("RegisterRequest", {
    "username": fields.String(required=True, description="Username"),
    "password": fields.String(required=True, description="Password"),
    "email": fields.String(required=False, description="Email"),
    "role": fields.String(required=False, description="Role", default="user"),
})

login_request = api.model("LoginRequest", {
    "username": fields.String(required=True, description="Username"),
    "password": fields.String(required=True, description="Password"),
})

login_response = api.model("LoginResponse", {
    "access_token": fields.String(description="JWT access token"),
    "user": fields.Nested(user_model, description="Authenticated user info"),
})

@api.route("/register")
class Register(Resource):
    @api.doc("user_register", description="Register new user")
    def post(self):
        """POST /api/auth/register — register a new user account"""
        import uuid
        data = request.json or {}
        username = data.get("username")
        password = data.get("password")
        role = data.get("role", "user")

        if not username or not password:
            abort(400, "Username and password required")

        if User.query.filter_by(username=username).first():
            abort(409, "User already exists")

        pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            password_hash=pw_hash,
            role=role,
        )
        db.session.add(user)
        db.session.commit()

        access_token = create_access_token(
            identity=user.id,
            additional_claims={"role": user.role}
        )

        return {
            "message": "User created successfully",
            "access_token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role
            }
        }, 201

@api.route("/login")
class Login(Resource):
    @api.doc("user_login", description="Authenticate and receive JWT token")
    @api.expect(login_request, validate=True)
    @api.marshal_with(login_response)
    def post(self):
        """POST /api/auth/login — returns {access_token, user}"""
        data = request.json
        username = data.get("username")
        password = data.get("password")
        
        user = User.query.filter_by(username=username).first()
        if not user:
            abort(401, "Invalid username or password")
            
        try:
            # Check password
            pw_hash = user.password_hash
            if not isinstance(pw_hash, bytes):
                pw_hash = pw_hash.encode("utf-8")
            if not bcrypt.checkpw(password.encode("utf-8"), pw_hash):
                abort(401, "Invalid username or password")
        except Exception as e:
            abort(401, "Invalid username or password")
            
        # Generate token with role claim
        access_token = create_access_token(
            identity=user.id,
            additional_claims={"role": user.role}
        )
        
        return {
            "access_token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role
            }
        }

@api.route("/me")
class CurrentUser(Resource):
    @api.doc("current_user", description="Get current authenticated user", security="Bearer")
    @jwt_required()
    @api.marshal_with(user_model)
    def get(self):
        """GET /api/auth/me — returns current user profile"""
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            abort(404, "User not found")
        return user
