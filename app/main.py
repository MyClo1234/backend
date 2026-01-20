from flask import Flask
from flask_cors import CORS
from app.core.config import Config
from app.routers.health_routes import health_bp
from app.routers.image_routes import image_bp
from app.routers.extraction_routes import extraction_bp
from app.routers.wardrobe_routes import wardrobe_bp
from app.routers.recommendation_routes import recommendation_bp

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Register Blueprints
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(image_bp, url_prefix='/api')
    app.register_blueprint(extraction_bp, url_prefix='/api')
    app.register_blueprint(wardrobe_bp, url_prefix='/api')
    app.register_blueprint(recommendation_bp, url_prefix='/api')
    
    return app

app = create_app()

if __name__ == '__main__':
    # Ensure config can only warn if generated
    Config.check_api_key()
    app.run(debug=True, port=5000, host='0.0.0.0')
