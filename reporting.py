from flask import Blueprint, render_template, request, jsonify, send_file, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.request import ServiceRequest, RequestComment
from app.models.directory import DirectoryCategory, DirectoryItem, FAQ
from app.models.user import User
from datetime import datetime, timedelta
from collections import Counter
import io

reporting_bp = Blueprint('reporting', __name__)


@reporting_bp.route('/')
@login_required
def index():
    """Главная страница - перенаправление на дашборд."""
    return redirect(url_for('reporting.dashboard'))


@reporting_bp.route('/dashboard')
@login_required
def dashboard():
    """Главная панель с основной статистикой."""
    # Общая статистика
    total_requests = ServiceRequest.query.count()
    new_requests = ServiceRequest.query.filter_by(status='new').count()
    in_progress = ServiceRequest.query.filter_by(status='in_progress').count()
    resolved_today = ServiceRequest.query.filter(
        ServiceRequest.status == 'resolved',
        ServiceRequest.resolved_at >= datetime.utcnow() - timedelta(days=1)
    ).count()
    
    # Запросы по статусам
    status_counts = db.session.query(
        ServiceRequest.status,
        db.func.count(ServiceRequest.id)
    ).group_by(ServiceRequest.status).all()
    
    # Запросы по приоритетам
    priority_counts = db.session.query(
        ServiceRequest.priority,
        db.func.count(ServiceRequest.id)
    ).group_by(ServiceRequest.priority).all()
    
    # Запросы за последние 7 дней
    last_7_days = []
    for i in range(7):
        day = datetime.utcnow() - timedelta(days=6-i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = ServiceRequest.query.filter(
            ServiceRequest.created_at >= day_start,
            ServiceRequest.created_at < day_end
        ).count()
        last_7_days.append({
            'date': day.strftime('%d.%m'),
            'count': count
        })
    
    # Топ исполнителей по количеству resolved запросов
    top_operators = db.session.query(
        User.full_name,
        db.func.count(ServiceRequest.id)
    ).join(
        ServiceRequest, ServiceRequest.assigned_to == User.id
    ).filter(
        ServiceRequest.status == 'resolved',
        User.role == 'operator'
    ).group_by(User.full_name).order_by(
        db.func.count(ServiceRequest.id).desc()
    ).limit(5).all()
    
    # Активные запросы текущего пользователя
    my_requests = ServiceRequest.query.filter_by(
        assigned_to=current_user.id
    ).filter(
        ServiceRequest.status.in_(['new', 'in_progress', 'on_hold'])
    ).order_by(
        ServiceRequest.priority.desc(),
        ServiceRequest.created_at
    ).limit(10).all()
    
    # Недавние запросы
    recent_requests = ServiceRequest.query.order_by(
        ServiceRequest.created_at.desc()
    ).limit(15).all()
    
    return render_template('reporting/dashboard.html',
                         total_requests=total_requests,
                         new_requests=new_requests,
                         in_progress=in_progress,
                         resolved_today=resolved_today,
                         status_counts=status_counts,
                         priority_counts=priority_counts,
                         last_7_days=last_7_days,
                         top_operators=top_operators,
                         my_requests=my_requests,
                         recent_requests=recent_requests)


@reporting_bp.route('/reports/statistics')
@login_required
def statistics():
    """Подробная статистика."""
    period = request.args.get('period', '30')  # days
    days = int(period)
    date_from = datetime.utcnow() - timedelta(days=days)
    
    # Запросы за период по дням
    daily_stats = []
    for i in range(days):
        day = date_from + timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = ServiceRequest.query.filter(
            ServiceRequest.created_at >= day_start,
            ServiceRequest.created_at < day_end
        ).count()
        daily_stats.append({
            'date': day.strftime('%d.%m.%Y'),
            'count': count
        })
    
    # Статистика по категориям
    category_stats = db.session.query(
        DirectoryCategory.name,
        db.func.count(ServiceRequest.id)
    ).outerjoin(
        ServiceRequest, ServiceRequest.category_id == DirectoryCategory.id
    ).group_by(
        DirectoryCategory.name
    ).order_by(
        db.func.count(ServiceRequest.id).desc()
    ).all()
    
    # Статистика по исполнителям
    operator_stats = db.session.query(
        User.full_name,
        User.username,
        db.func.count(ServiceRequest.id).label('total'),
        db.func.sum(db.case((ServiceRequest.status == 'resolved', 1), else_=0)).label('resolved'),
        db.func.avg(
            db.case(
                (ServiceRequest.status == 'resolved', 
                 db.cast(ServiceRequest.resolved_at - ServiceRequest.created_at, db.Integer)),
                else_=0
            )
        ).label('avg_hours')
    ).outerjoin(
        ServiceRequest, ServiceRequest.assigned_to == User.id
    ).filter(
        ServiceRequest.created_at >= date_from,
        User.role == 'operator'
    ).group_by(
        User.id, User.full_name, User.username
    ).order_by(
        db.func.count(ServiceRequest.id).desc()
    ).all()
    
    # Среднее время разрешения
    avg_resolution = db.session.query(
        db.func.avg(
            db.cast(ServiceRequest.resolved_at - ServiceRequest.created_at, db.Integer)
        )
    ).filter(
        ServiceRequest.status == 'resolved',
        ServiceRequest.resolved_at.isnot(None),
        ServiceRequest.created_at >= date_from
    ).first()
    
    return render_template('reporting/statistics.html',
                         days=days,
                         daily_stats=daily_stats,
                         category_stats=category_stats,
                         operator_stats=operator_stats,
                         avg_resolution=avg_resolution)


@reporting_bp.route('/reports/export')
@login_required
def export_report():
    """Экспорт отчёта в CSV."""
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = ServiceRequest.query
    
    if status:
        query = query.filter_by(status=status)
    if date_from:
        query = query.filter(ServiceRequest.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    if date_to:
        query = query.filter(ServiceRequest.created_at <= datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1))
    
    requests = query.order_by(ServiceRequest.created_at.desc()).all()
    
    # Формирование CSV
    output = io.StringIO()
    output.write('№,Дата,Номер,Тема,Статус,Приоритет,Исполнитель,Клиент,Телефон\n')
    
    for req in requests:
        assignee = User.query.get(req.assigned_to).full_name if req.assigned_to else 'Не назначен'
        output.write(f'{req.id},{req.created_at.strftime("%Y-%m-%d %H:%M")},{req.request_number},'
                    f'"{req.title}",{req.get_status_display()},{req.get_priority_display()},'
                    f'"{assignee}","{req.client_name or ""}","{req.client_phone or ""}"\n')
    
    output.seek(0)
    
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=requests_report.csv'}
    )


@reporting_bp.route('/api/stats/requests-by-status')
@login_required
def api_requests_by_status():
    """API: статистика запросов по статусам."""
    status_counts = db.session.query(
        ServiceRequest.status,
        db.func.count(ServiceRequest.id)
    ).group_by(ServiceRequest.status).all()
    
    data = {status: count for status, count in status_counts}
    return jsonify(data)


@reporting_bp.route('/api/stats/requests-by-priority')
@login_required
def api_requests_by_priority():
    """API: статистика запросов по приоритетам."""
    priority_counts = db.session.query(
        ServiceRequest.priority,
        db.func.count(ServiceRequest.id)
    ).group_by(ServiceRequest.priority).all()
    
    data = {priority: count for priority, count in priority_counts}
    return jsonify(data)


@reporting_bp.route('/api/stats/trending')
@login_required
def api_trending():
    """API: тренд запросов за последние 7 дней."""
    last_7_days = []
    for i in range(7):
        day = datetime.utcnow() - timedelta(days=6-i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = ServiceRequest.query.filter(
            ServiceRequest.created_at >= day_start,
            ServiceRequest.created_at < day_end
        ).count()
        last_7_days.append({
            'date': day.strftime('%d.%m'),
            'count': count
        })
    
    return jsonify(last_7_days)
