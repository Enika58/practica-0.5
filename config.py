import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Базовая конфигурация приложения."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///spravka.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB


class DevelopmentConfig(Config):
    """Конфигурация для среды разработки."""
    DEBUG = True


class ProductionConfig(Config):
    """Конфигурация для продакшн-среды."""
    DEBUG = False
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set for production")


class TestingConfig(Config):
    """Конфигурация для тестирования."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
