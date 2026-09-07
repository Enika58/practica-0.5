from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.request import ServiceRequest, RequestComment, RequestHistory
from app.models.directory import DirectoryCategory, ServiceType
from app.models.user import User
from datetime import datetime
import re

requests_bp = Blueprint('requests', __name__)


def generate_request_number():
    """Генерация уникального номера запроса."""
    today = datetime.utcnow().strftime('%Y%m%d')
    count = ServiceRequest.query.filter(
        ServiceRequest.request_number.like(f'{today}%')
    ).count()
    return f'{today}-{str(count + 1).zfill(4)}'


def log_request_history(request_id, action, field_name=None, old_value=None, 
                       new_value=None, user_id=None):
    """Логирование изменения в запросе."""
    history = RequestHistory(
        request_id=request_id,
        user_id=user_id or current_user.id,
        action=action,
        field_name=field_name,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None
    )
    db.session.add(history)
    db.session.commit()


@requests_bp.route('/requests')
@login_required
def requests_list():
    """Список всех запросов."""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    search = request.args.get('search', '').strip()
    assigned = request.args.get('assigned', '')  # 'me' или ID пользователя
    
    query = ServiceRequest.query
    
    # Фильтрация по статусу
    if status:
        query = query.filter_by(status=status)
    
    # Фильтрация по приоритету
    if priority:
        query = query.filter_by(priority=priority)
    
    # Поиск
    if search:
        query = query.filter(
            db.or_(
                ServiceRequest.title.ilike(f'%{search}%'),
                ServiceRequest.request_number.ilike(f'%{search}%'),
                ServiceRequest.client_name.ilike(f'%{search}%')
            )
        )
    
    # Фильтрация по исполнителю
    if assigned == 'me':
        query = query.filter_by(assigned_to=current_user.id)
    elif assigned and assigned != 'all':
        query = query.filter_by(assigned_to=int(assigned))
    
    requests = query.order_by(
        ServiceRequest.priority.desc(),
        ServiceRequest.created_at.desc()
    ).paginate(page=page, per_page=25)
    
    categories = DirectoryCategory.query.filter_by(is_active=True).all()
    service_types = ServiceType.query.filter_by(is_active=True).all()
    users = User.query.filter(User.is_active == True, User.role != 'admin').all()
    
    # Статистика
    stats = {
        'new': ServiceRequest.query.filter_by(status='new').count(),
        'in_progress': ServiceRequest.query.filter_by(status='in_progress').count(),
        'resolved': ServiceRequest.query.filter_by(status='resolved').count(),
        'my_tasks': ServiceRequest.query.filter_by(
            assigned_to=current_user.id, 
            status='in_progress'
        ).count()
    }
    
    return render_template('requests/list.html', requests=requests, 
                         categories=categories, service_types=service_types,
                         users=users, search=search, status=status,
                         priority=priority, assigned=assigned, stats=stats)


@requests_bp.route('/requests/create', methods=['GET', 'POST'])
@login_required
def create_request():
    """Создание нового запроса."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        client_name = request.form.get('client_name', '').strip()
        client_phone = request.form.get('client_phone', '').strip()
        client_email = request.form.get('client_email', '').strip()
        category_id = request.form.get('category_id', type=int)
        service_type_id = request.form.get('service_type_id', type=int)
        priority = request.form.get('priority', 'medium')
        source = request.form.get('source', 'phone')
        tags = request.form.get('tags', '').strip()
        
        if not title or not description:
            flash('Заполните обязательные поля', 'danger')
            return render_template('requests/create.html', 
                                 categories=DirectoryCategory.query.filter_by(is_active=True).all(),
                                 service_types=ServiceType.query.filter_by(is_active=True).all())
        
        request_obj = ServiceRequest(
            request_number=generate_request_number(),
            title=title,
            description=description,
            client_name=client_name or None,
            client_phone=client_phone or None,
            client_email=client_email or None,
            category_id=category_id,
            service_type_id=service_type_id,
            priority=priority,
            source=source,
            tags=tags or None,
            created_by=current_user.id
        )
        
        db.session.add(request_obj)
        db.session.commit()
        
        log_request_history(request_obj.id, 'created', 
                          old_value=None, new_value='new')
        
        flash(f'Запрос {request_obj.request_number} создан', 'success')
        return redirect(url_for('requests.request_detail', request_id=request_obj.id))
    
    categories = DirectoryCategory.query.filter_by(is_active=True).all()
    service_types = ServiceType.query.filter_by(is_active=True).all()
    return render_template('requests/create.html', 
                         categories=categories, service_types=service_types)


@requests_bp.route('/requests/<int:request_id>')
@login_required
def request_detail(request_id):
    """Детали запроса."""
    request_obj = ServiceRequest.query.get_or_404(request_id)
    comments = RequestComment.query.filter_by(request_id=request_id)\
        .order_by(RequestComment.created_at).all()
    history = RequestHistory.query.filter_by(request_id=request_id)\
        .order_by(RequestHistory.created_at).all()
    
    return render_template('requests/detail.html', 
                         request=request_obj, comments=comments, history=history)


@requests_bp.route('/requests/<int:request_id>/update', methods=['POST'])
@login_required
def update_request(request_id):
    """Обновление запроса."""
    request_obj = ServiceRequest.query.get_or_404(request_id)
    
    old_status = request_obj.status
    
    # Обновление полей
    request_obj.title = request.form.get('title', '').strip() or request_obj.title
    request_obj.description = request.form.get('description', '').strip() or request_obj.description
    request_obj.client_name = request.form.get('client_name', '').strip() or None
    request_obj.client_phone = request.form.get('client_phone', '').strip() or None
    request_obj.client_email = request.form.get('client_email', '').strip() or None
    request_obj.priority = request.form.get('priority', request_obj.priority)
    request_obj.tags = request.form.get('tags', '').strip() or None
    
    # Изменение статуса
    new_status = request.form.get('status', '')
    if new_status and new_status != old_status:
        old_status_text = request_obj.get_status_display()
        request_obj.status = new_status
        new_status_text = request_obj.get_status_display()
        
        if new_status in ('resolved', 'closed'):
            now = datetime.utcnow()
            if new_status == 'resolved':
                request_obj.resolved_at = now
            else:
                request_obj.closed_at = now
        
        log_request_history(request_obj.id, 'status_change', 
                          'status', old_status_text, new_status_text)
    
    # Изменение исполнителя
    assigned_to = request.form.get('assigned_to', type=int)
    if assigned_to and assigned_to != request_obj.assigned_to:
        old_assignee = User.query.get(request_obj.assigned_to)
        new_assignee = User.query.get(assigned_to)
        log_request_history(request_obj.id, 'assign',
                          'assignee',
                          old_assignee.username if old_assignee else None,
                          new_assignee.username if new_assignee else None)
        request_obj.assigned_to = assigned_to
    
    db.session.commit()
    flash('Запрос обновлён', 'success')
    return redirect(url_for('requests.request_detail', request_id=request_id))


@requests_bp.route('/requests/<int:request_id>/comment', methods=['POST'])
@login_required
def add_comment(request_id):
    """Добавление комментария."""
    request_obj = ServiceRequest.query.get_or_404(request_id)
    text = request.form.get('text', '').strip()
    is_internal = request.form.get('is_internal', type=int) == 1
    
    if not text:
        flash('Текст комментария не может быть пустым', 'danger')
        return redirect(url_for('requests.request_detail', request_id=request_id))
    
    comment = RequestComment(
        request_id=request_id,
        user_id=current_user.id,
        text=text,
        is_internal=is_internal
    )
    db.session.add(comment)
    
    # Автоматическая смена статуса на "В работе" при первом комментарии
    if request_obj.status == 'new':
        request_obj.status = 'in_progress'
        log_request_history(request_obj.id, 'status_change', 
                          'status', 'Новый', 'В работе')
    
    db.session.commit()
    flash('Комментарий добавлен', 'success')
    return redirect(url_for('requests.request_detail', request_id=request_id))


@requests_bp.route('/requests/<int:request_id>/delete', methods=['POST'])
@login_required
def delete_request(request_id):
    """Удаление запроса (только для администраторов и менеджеров)."""
    if not current_user.can_manage('operator'):
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('requests.requests_list'))
    
    request_obj = ServiceRequest.query.get_or_404(request_id)
    number = request_obj.request_number
    db.session.delete(request_obj)
    db.session.commit()
    flash(f'Запрос {number} удалён', 'info')
    return redirect(url_for('requests.requests_list'))


# ==================== API для AJAX ====================

@requests_bp.route('/api/requests/assign', methods=['POST'])
@login_required
def api_assign():
    """API для назначения исполнителя (AJAX)."""
    data = request.get_json()
    request_id = data.get('request_id')
    user_id = data.get('user_id')
    
    request_obj = ServiceRequest.query.get_or_404(request_id)
    old_assignee = User.query.get(request_obj.assigned_to)
    new_assignee = User.query.get(user_id)
    
    request_obj.assigned_to = user_id
    if request_obj.status == 'new':
        request_obj.status = 'in_progress'
    
    log_request_history(request_obj.id, 'assign',
                      'assignee',
                      old_assignee.username if old_assignee else None,
                      new_assignee.username if new_assignee else None)
    
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Исполнитель назначен'})


@requests_bp.route('/api/requests/bulk-action', methods=['POST'])
@login_required
def bulk_action():
    """Массовые действия с запросами."""
    data = request.get_json()
    request_ids = data.get('request_ids', [])
    action = data.get('action', '')
    
    count = 0
    for req_id in request_ids:
        req = ServiceRequest.query.get(req_id)
        if req and req.status != 'closed':
            if action == 'assign_me':
                req.assigned_to = current_user.id
                if req.status == 'new':
                    req.status = 'in_progress'
                count += 1
            elif action == 'resolve':
                req.resolve()
                count += 1
    
    if count > 0:
        db.session.commit()
    
    return jsonify({'status': 'success', 'processed': count})
