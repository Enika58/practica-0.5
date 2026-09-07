from datetime import datetime
from app import db


class ServiceRequest(db.Model):
    """
    Модель обращения/запроса клиента.
    
    Статусы: new, in_progress, on_hold, resolved, closed, rejected
    Приоритеты: low, medium, high, critical
    """
    __tablename__ = 'service_requests'

    id = db.Column(db.Integer, primary_key=True)
    request_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Классификация
    category_id = db.Column(db.Integer, db.ForeignKey('directory_categories.id'), nullable=True)
    service_type_id = db.Column(db.Integer, db.ForeignKey('service_types.id'), nullable=True)
    tags = db.Column(db.String(300), nullable=True)  # Теги через запятую
    
    # Статус и приоритет
    status = db.Column(db.String(20), nullable=False, default='new', index=True)
    priority = db.Column(db.String(20), nullable=False, default='medium')
    # statuses: new, in_progress, on_hold, resolved, closed, rejected
    # priorities: low, medium, high, critical
    
    # Контактные данные клиента
    client_name = db.Column(db.String(120), nullable=True)
    client_phone = db.Column(db.String(20), nullable=True)
    client_email = db.Column(db.String(120), nullable=True)
    
    # Назначение и обработка
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    
    # Дополнительная информация
    source = db.Column(db.String(50), default='phone')  # phone, email, web, walk-in
    external_id = db.Column(db.String(100), nullable=True)
    
    # Связи
    comments = db.relationship('RequestComment', backref='request', lazy='dynamic',
                              cascade='all, delete-orphan',
                              order_by='RequestComment.created_at')

    def resolve(self):
        """Разрешение запроса."""
        self.status = 'resolved'
        self.resolved_at = datetime.utcnow()

    def close(self):
        """Закрытие запроса."""
        self.status = 'closed'
        self.closed_at = datetime.utcnow()

    def get_status_display(self):
        """Получение отображаемого названия статуса."""
        statuses = {
            'new': 'Новый',
            'in_progress': 'В работе',
            'on_hold': 'На паузе',
            'resolved': 'Решён',
            'closed': 'Закрыт',
            'rejected': 'Отклонён'
        }
        return statuses.get(self.status, self.status)

    def get_priority_display(self):
        """Получение отображаемого названия приоритета."""
        priorities = {
            'low': 'Низкий',
            'medium': 'Средний',
            'high': 'Высокий',
            'critical': 'Критический'
        }
        return priorities.get(self.priority, self.priority)

    def get_priority_class(self):
        """CSS класс для приоритета."""
        return f'priority-{self.priority}'

    def __repr__(self):
        return f'<ServiceRequest {self.request_number}>'


class RequestComment(db.Model):
    """Модель комментария к запросу."""
    __tablename__ = 'request_comments'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('service_requests.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    is_internal = db.Column(db.Boolean, default=False)  # Внутренний комментарий
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь
    user = db.relationship('User', backref='comments')

    def __repr__(self):
        return f'<RequestComment {self.id} by User {self.user_id}>'


class RequestHistory(db.Model):
    """Модель истории изменений запроса."""
    __tablename__ = 'request_history'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('service_requests.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)  # status_change, assign, comment, etc.
    field_name = db.Column(db.String(50), nullable=True)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='request_history')

    def __repr__(self):
        return f'<RequestHistory {self.action} on Request {self.request_id}>'
