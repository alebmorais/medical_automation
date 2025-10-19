"""Route blueprints for Medical Automation Suite."""
from .medical_routes import medical_bp
from .snippet_routes import snippet_bp

__all__ = ["medical_bp", "snippet_bp"]