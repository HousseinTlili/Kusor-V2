"""Global error handlers for the Flask app."""
from flask import jsonify
from werkzeug.exceptions import HTTPException

def register_error_handlers(app):
    """Register error handlers for 400, 401, 403, 404, 500."""
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Return JSON instead of HTML for HTTP errors."""
        response = e.get_response()
        # Create JSON response
        data = {
            "code": e.code,
            "name": e.name,
            "description": e.description,
        }
        response.data = jsonify(data).data
        response.content_type = "application/json"
        return response

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        """Log the error and return a 500 error response."""
        import sys
        import traceback
        import jwt
        from flask_jwt_extended.exceptions import JWTExtendedException
        
        # Gracefully handle JWT expiration or validation errors to return 401 instead of 500
        if isinstance(e, jwt.exceptions.ExpiredSignatureError):
            return jsonify({
                "code": 401,
                "name": "Unauthorized",
                "description": "Token has expired. Please log in again."
            }), 401
            
        if isinstance(e, (jwt.exceptions.PyJWTError, JWTExtendedException)):
            return jsonify({
                "code": 401,
                "name": "Unauthorized",
                "description": str(e)
            }), 401

        print(f"Unhandled system error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        
        data = {
            "code": 500,
            "name": "Internal Server Error",
            "description": "An unexpected error occurred on the server.",
        }
        return jsonify(data), 500

