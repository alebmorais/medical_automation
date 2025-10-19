"""Server module for Medical Automation Suite."""
import sys
from ..config import config
from ..utils.logger import setup_logger
from .app import create_app

logger = setup_logger(__name__, "server.log")


def main():
    """Main entry point for the server."""
    try:
        # Validate configuration
        config.validate()
        
        # Create Flask app
        app = create_app()
        
        # Run server
        logger.info(
            f"Starting Medical Automation Server on "
            f"{config.SERVER_HOST}:{config.MEDICAL_SERVER_PORT}"
        )
        
        app.run(
            host=config.SERVER_HOST,
            port=config.MEDICAL_SERVER_PORT,
            debug=config.DEBUG
        )
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()