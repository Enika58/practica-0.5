from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
import hashlib
import secrets


class User(UserMixin, db.Model):
    """Модель пользователя системы."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='operator')
    # roles: admin, manager, operator
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    # Связи
    requests = db.relationship('ServiceRequest', backref='assignee', lazy='dynamic',
                              foreign_keys='ServiceRequest.assigned_to')
    created_requests = db.relationship('ServiceRequest', backref='creator', lazy='dynamic',
                                      foreign_keys='ServiceRequest.created_by')

    def set_password(self, password):
        """Установка пароля с хешированием."""
        self.password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    def check_password(self, password):
        """Проверка пароля."""
        return self.password_hash == hashlib.sha256(password.encode('utf-8')).hexdigest()

    def is_locked(self):
        """Проверка, заблокирован ли пользователь."""
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        # Снятие блокировки по истечении времени
        if self.locked_until and datetime.utcnow() >= self.locked_until:
            self.failed_login_attempts = 0
            self.locked_until = None
            db.session.commit()
        return False

    def lock_account(self, minutes=30):
        """Блокировка аккаунта после неудачных попыток."""
        from datetime import timedelta
        self.failed_login_attempts += 1
        self.locked_until = datetime.utcnow() + timedelta(minutes=minutes)
        db.session.commit()

    def reset_failed_attempts(self):
        """Сброс счётчика неудачных попыток."""
        self.failed_login_attempts = 0
        self.locked_until = None
        db.session.commit()

    def can_manage(self, target_role):
        """Проверка прав на управление пользователями с указанной ролью."""
        role_hierarchy = {'admin': 3, 'manager': 2, 'operator': 1}
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(target_role, 0)

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    """Загрузка пользователя по ID для Flask-Login."""
    return User.query.get(int(user_id))
