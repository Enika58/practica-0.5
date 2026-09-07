from datetime import datetime
from app import db


class DirectoryCategory(db.Model):
    """Модель категорий справочной информации."""
    __tablename__ = 'directory_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('directory_categories.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи для иерархии
    parent = db.relationship('DirectoryCategory', remote_side=[id], backref='subcategories')
    items = db.relationship('DirectoryItem', backref='category', lazy='dynamic',
                           cascade='all, delete-orphan')

    def __repr__(self):
        return f'<DirectoryCategory {self.name}>'


class DirectoryItem(db.Model):
    """Модель элемента справочной информации."""
    __tablename__ = 'directory_items'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('directory_categories.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    keywords = db.Column(db.String(500), nullable=True)  # Ключевые слова для поиска
    priority = db.Column(db.Integer, default=0)  # Приоритет отображения
    is_published = db.Column(db.Boolean, default=True)
    views_count = db.Column(db.Integer, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<DirectoryItem {self.title}>'


class ServiceType(db.Model):
    """Модель типов услуг/услуг."""
    __tablename__ = 'service_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    code = db.Column(db.String(20), unique=True, nullable=True)  # Код услуги
    duration_minutes = db.Column(db.Integer, nullable=True)  # Среднее время обработки
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ServiceType {self.name}>'


class FAQ(db.Model):
    """Модель часто задаваемых вопросов."""
    __tablename__ = 'faqs'

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False, index=True)
    answer = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('directory_categories.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    views_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<FAQ {self.question[:50]}>'
