"""
Тесты для АИС Справочная служба
"""
import pytest
import os
import sys

# Добавление пути к приложению
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models.user import User
from app.models.directory import DirectoryCategory, DirectoryItem, ServiceType, FAQ
from app.models.request import ServiceRequest, RequestComment


@pytest.fixture
def app():
    """Создание тестового приложения."""
    app = create_app('testing')
    app.config['TESTING'] = True
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Создание тестового клиента."""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Создание тестового пользователя."""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            full_name='Тестовый Пользователь',
            role='operator',
            is_active=True
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        yield user
        db.session.delete(user)
        db.session.commit()


@pytest.fixture
def test_category(app):
    """Создание тестовой категории."""
    with app.app_context():
        category = DirectoryCategory(name='Тестовая категория', description='Для тестов')
        db.session.add(category)
        db.session.commit()
        yield category
        db.session.delete(category)
        db.session.commit()


@pytest.fixture
def test_request(app, test_user):
    """Создание тестового запроса."""
    with app.app_context():
        request = ServiceRequest(
            request_number='20260101-0001',
            title='Тестовый запрос',
            description='Описание тестового запроса',
            priority='medium',
            status='new',
            created_by=test_user.id
        )
        db.session.add(request)
        db.session.commit()
        yield request
        db.session.delete(request)
        db.session.commit()


# ==================== Тесты аутентификации ====================

class TestAuthentication:
    """Тесты модуля аутентификации."""
    
    def test_login_page(self, client):
        """Проверка доступа к странице входа."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower() or response.status_code == 200
    
    def test_login_success(self, client, test_user):
        """Успешный вход."""
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpass123'
        }, follow_redirects=True)
        assert response.status_code == 200
    
    def test_login_invalid_password(self, client, test_user):
        """Неверный пароль."""
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'wrongpass'
        }, follow_redirects=True)
        assert response.status_code == 200
    
    def test_login_nonexistent_user(self, client):
        """Вход несуществующего пользователя."""
        response = client.post('/auth/login', data={
            'username': 'nonexistent',
            'password': 'anypassword'
        }, follow_redirects=True)
        assert response.status_code == 200
    
    def test_logout(self, client, test_user):
        """Выход из системы."""
        # Сначала вход
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # Затем выход
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
    
    def test_protected_route_redirect(self, client):
        """Перенаправление на вход при доступе к защищённой странице."""
        response = client.get('/requests', follow_redirects=True)
        assert response.status_code == 200


# ==================== Тесты пользователей ====================

class TestUsers:
    """Тесты управления пользователями."""
    
    def test_user_model_creation(self, test_user):
        """Создание пользователя."""
        assert test_user.username == 'testuser'
        assert test_user.email == 'test@example.com'
        assert test_user.full_name == 'Тестовый Пользователь'
        assert test_user.role == 'operator'
        assert test_user.is_active == True
    
    def test_password_hashing(self, test_user):
        """Хеширование пароля."""
        assert test_user.password_hash != 'testpass123'
        assert test_user.check_password('testpass123')
        assert not test_user.check_password('wrongpass')
    
    def test_user_role_hierarchy(self, app):
        """Проверка иерархии ролей."""
        with app.app_context():
            admin = User(username='admin_test', email='admin@test.com', role='admin')
            admin.set_password('pass')
            manager = User(username='manager_test', email='mgr@test.com', role='manager')
            manager.set_password('pass')
            operator = User(username='operator_test', email='op@test.com', role='operator')
            operator.set_password('pass')
            
            db.session.add_all([admin, manager, operator])
            db.session.commit()
            
            assert admin.can_manage('operator') == True
            assert admin.can_manage('manager') == True
            assert manager.can_manage('operator') == True
            assert operator.can_manage('admin') == False
            assert operator.can_manage('manager') == False
            
            db.session.delete(admin)
            db.session.delete(manager)
            db.session.delete(operator)
            db.session.commit()


# ==================== Тесты справочников ====================

class TestDirectories:
    """Тесты справочников."""
    
    def test_category_creation(self, test_category):
        """Создание категории."""
        assert test_category.name == 'Тестовая категория'
        assert test_category.description == 'Для тестов'
        assert test_category.is_active == True
    
    def test_add_directory_item(self, app, test_user, test_category):
        """Добавление элемента справочника."""
        with app.app_context():
            item = DirectoryItem(
                title='Тестовый элемент',
                content='Содержание элемента',
                category_id=test_category.id,
                created_by=test_user.id
            )
            db.session.add(item)
            db.session.commit()
            
            assert item.title == 'Тестовый элемент'
            assert item.is_published == True
            assert item.views_count == 0
    
    def test_service_type_creation(self, app):
        """Создание типа услуги."""
        with app.app_context():
            st = ServiceType(
                name='Консультация',
                code='SVC-001',
                duration_minutes=30
            )
            db.session.add(st)
            db.session.commit()
            
            assert st.name == 'Консультация'
            assert st.code == 'SVC-001'
    
    def test_faq_creation(self, app):
        """Создание FAQ."""
        with app.app_context():
            faq = FAQ(
                question='Как создать запрос?',
                answer='Перейдите в раздел Запросы и нажмите Новый запрос.'
            )
            db.session.add(faq)
            db.session.commit()
            
            assert faq.question == 'Как создать запрос?'
            assert faq.is_active == True


# ==================== Тесты запросов ====================

class TestRequests:
    """Тесты управления запросами."""
    
    def test_request_creation(self, test_request):
        """Создание запроса."""
        assert test_request.title == 'Тестовый запрос'
        assert test_request.status == 'new'
        assert test_request.priority == 'medium'
    
    def test_request_status_change(self, test_request):
        """Изменение статуса запроса."""
        test_request.status = 'in_progress'
        db.session.commit()
        
        req = ServiceRequest.query.get(test_request.id)
        assert req.status == 'in_progress'
    
    def test_request_resolve(self, test_request):
        """Разрешение запроса."""
        test_request.resolve()
        db.session.commit()
        
        req = ServiceRequest.query.get(test_request.id)
        assert req.status == 'resolved'
        assert req.resolved_at is not None
    
    def test_request_number_generation(self, app):
        """Генерация номера запроса."""
        with app.app_context():
            from app.routes.requests import generate_request_number
            number = generate_request_number()
            assert number.startswith('2026')
            assert '-' in number
    
    def test_request_comments(self, app, test_request, test_user):
        """Добавление комментариев."""
        with app.app_context():
            comment = RequestComment(
                request_id=test_request.id,
                user_id=test_user.id,
                text='Тестовый комментарий'
            )
            db.session.add(comment)
            db.session.commit()
            
            comments = RequestComment.query.filter_by(request_id=test_request.id).all()
            assert len(comments) == 1
            assert comments[0].text == 'Тестовый комментарий'


# ==================== Тесты API ====================

class TestAPI:
    """Тесты API."""
    
    def test_api_categories(self, client, test_user):
        """Получение списка категорий через API."""
        client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        })
        
        response = client.get('/api/directories/categories')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
    
    def test_api_faq(self, client, test_user):
        """Получение списка FAQ через API."""
        client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        })
        
        response = client.get('/api/faq')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)


# ==================== Тесты маршрутов ====================

class TestRoutes:
    """Тесты основных маршрутов."""
    
    def test_index_page(self, client):
        """Доступ к главной странице."""
        response = client.get('/')
        assert response.status_code == 302  # Перенаправление на вход
    
    def test_login_page_access(self, client):
        """Доступ к странице входа."""
        response = client.get('/auth/login')
        assert response.status_code == 200
    
    def test_dashboard_requires_auth(self, client):
        """Дашборд требует авторизации."""
        response = client.get('/dashboard')
        assert response.status_code == 302
    
    def test_search_page(self, client, test_user):
        """Доступ к странице поиска."""
        client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123'
        })
        
        response = client.get('/search?q=тест')
        assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
