"""
АИС Справочная служба - Главный файл запуска
"""
import os
from app import create_app

# Создание приложения
app = create_app(os.environ.get('FLASK_CONFIG', 'development'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
