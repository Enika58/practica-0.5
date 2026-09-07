from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.directory import DirectoryCategory, DirectoryItem, ServiceType, FAQ
from app.models.request import ServiceRequest
from datetime import datetime

directories_bp = Blueprint('directories', __name__)


# ==================== Категории ====================

@directories_bp.route('/categories')
@login_required
def categories():
    """Управление категориями справочника."""
    categories = DirectoryCategory.query.order_by(DirectoryCategory.name).all()
    return render_template('directories/categories.html', categories=categories)


@directories_bp.route('/categories/add', methods=['POST'])
@login_required
def add_category():
    """Добавление категории."""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    parent_id = request.form.get('parent_id', type=int)

    if not name:
        flash('Название категории обязательно', 'danger')
        return redirect(url_for('directories.categories'))

    category = DirectoryCategory(
        name=name,
        description=description,
        parent_id=parent_id if parent_id != '' else None,
        is_active=True
    )
    db.session.add(category)
    db.session.commit()
    flash(f'Категория "{name}" добавлена', 'success')
    return redirect(url_for('directories.categories'))


@directories_bp.route('/categories/<int:category_id>/update', methods=['POST'])
@login_required
def update_category(category_id):
    """Обновление категории."""
    category = DirectoryCategory.query.get_or_404(category_id)
    category.name = request.form.get('name', '').strip() or category.name
    category.description = request.form.get('description', '').strip() or category.description
    category.is_active = request.form.get('is_active', type=int) == 1
    category.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Категория обновлена', 'success')
    return redirect(url_for('directories.categories'))


@directories_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    """Удаление категории."""
    category = DirectoryCategory.query.get_or_404(category_id)
    name = category.name
    db.session.delete(category)
    db.session.commit()
    flash(f'Категория "{name}" удалена', 'info')
    return redirect(url_for('directories.categories'))


# ==================== Элементы справочника ====================

@directories_bp.route('/items')
@login_required
def items():
    """Управление элементами справочника."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', type=int)
    
    query = DirectoryItem.query.filter_by(is_published=True)
    
    if search:
        query = query.filter(
            db.or_(
                DirectoryItem.title.ilike(f'%{search}%'),
                DirectoryItem.content.ilike(f'%{search}%'),
                DirectoryItem.keywords.ilike(f'%{search}%')
            )
        )
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    items = query.order_by(DirectoryItem.priority.desc(), DirectoryItem.created_at.desc())\
        .paginate(page=page, per_page=20)
    
    categories = DirectoryCategory.query.filter_by(is_active=True).all()
    return render_template('directories/items.html', items=items, categories=categories,
                         search=search, category_id=category_id)


@directories_bp.route('/items/add', methods=['POST'])
@login_required
def add_item():
    """Добавление элемента справочника."""
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    category_id = request.form.get('category_id', type=int)
    keywords = request.form.get('keywords', '').strip()
    priority = request.form.get('priority', 0, type=int)

    if not title or not content or not category_id:
        flash('Заполните обязательные поля', 'danger')
        return redirect(url_for('directories.items'))

    item = DirectoryItem(
        title=title,
        content=content,
        category_id=category_id,
        keywords=keywords,
        priority=priority,
        is_published=True,
        created_by=current_user.id
    )
    db.session.add(item)
    db.session.commit()
    
    # Увеличение счётчика просмотров
    item.views_count += 1
    db.session.commit()
    
    flash(f'Элемент "{title}" добавлен', 'success')
    return redirect(url_for('directories.items'))


@directories_bp.route('/items/<int:item_id>/view')
@login_required
def view_item(item_id):
    """Просмотр элемента справочника."""
    item = DirectoryItem.query.get_or_404(item_id)
    item.views_count += 1
    db.session.commit()
    return render_template('directories/item_view.html', item=item)


@directories_bp.route('/items/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    """Удаление элемента справочника."""
    item = DirectoryItem.query.get_or_404(item_id)
    title = item.title
    db.session.delete(item)
    db.session.commit()
    flash(f'Элемент "{title}" удалён', 'info')
    return redirect(url_for('directories.items'))


# ==================== Типы услуг ====================

@directories_bp.route('/service-types')
@login_required
def service_types():
    """Управление типами услуг."""
    types = ServiceType.query.order_by(ServiceType.name).all()
    return render_template('directories/service_types.html', types=types)


@directories_bp.route('/service-types/add', methods=['POST'])
@login_required
def add_service_type():
    """Добавление типа услуги."""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    code = request.form.get('code', '').strip()
    duration = request.form.get('duration_minutes', type=int)

    if not name:
        flash('Название обязательно', 'danger')
        return redirect(url_for('directories.service_types'))

    service_type = ServiceType(
        name=name,
        description=description,
        code=code if code else None,
        duration_minutes=duration if duration else None
    )
    db.session.add(service_type)
    db.session.commit()
    flash(f'Тип услуги "{name}" добавлен', 'success')
    return redirect(url_for('directories.service_types'))


@directories_bp.route('/service-types/<int:type_id>/toggle', methods=['POST'])
@login_required
def toggle_service_type(type_id):
    """Переключение активности типа услуги."""
    st = ServiceType.query.get_or_404(type_id)
    st.is_active = not st.is_active
    db.session.commit()
    return redirect(url_for('directories.service_types'))


# ==================== FAQ ====================

@directories_bp.route('/faqs')
@login_required
def faqs():
    """Управление FAQ."""
    faqs_list = FAQ.query.order_by(FAQ.views_count.desc()).all()
    categories = DirectoryCategory.query.filter_by(is_active=True).all()
    return render_template('directories/faqs.html', faqs=faqs_list, categories=categories)


@directories_bp.route('/faqs/add', methods=['POST'])
@login_required
def add_faq():
    """Добавление вопроса-ответа."""
    question = request.form.get('question', '').strip()
    answer = request.form.get('answer', '').strip()
    category_id = request.form.get('category_id', type=int)

    if not question or not answer:
        flash('Заполните все обязательные поля', 'danger')
        return redirect(url_for('directories.faqs'))

    faq = FAQ(
        question=question,
        answer=answer,
        category_id=category_id if category_id else None
    )
    db.session.add(faq)
    db.session.commit()
    flash('Вопрос-ответ добавлен', 'success')
    return redirect(url_for('directories.faqs'))


@directories_bp.route('/faqs/<int:faq_id>/toggle', methods=['POST'])
@login_required
def toggle_faq(faq_id):
    """Переключение активности FAQ."""
    faq = FAQ.query.get_or_404(faq_id)
    faq.is_active = not faq.is_active
    db.session.commit()
    return redirect(url_for('directories.faqs'))


# ==================== Поиск ====================

@directories_bp.route('/search')
@login_required
def search():
    """Глобальный поиск по справочнику."""
    query_text = request.args.get('q', '').strip()
    
    if not query_text:
        return render_template('directories/search.html', results=[], total=0)
    
    # Поиск по элементам справочника
    items = DirectoryItem.query.filter(
        DirectoryItem.is_published == True,
        db.or_(
            DirectoryItem.title.ilike(f'%{query_text}%'),
            DirectoryItem.content.ilike(f'%{query_text}%'),
            DirectoryItem.keywords.ilike(f'%{query_text}%')
        )
    ).order_by(DirectoryItem.priority.desc()).limit(20).all()
    
    # Поиск по FAQ
    faqs = FAQ.query.filter(
        FAQ.is_active == True,
        db.or_(
            FAQ.question.ilike(f'%{query_text}%'),
            FAQ.answer.ilike(f'%{query_text}%')
        )
    ).limit(10).all()
    
    # Поиск по запросам
    requests = ServiceRequest.query.filter(
        db.or_(
            ServiceRequest.title.ilike(f'%{query_text}%'),
            ServiceRequest.description.ilike(f'%{query_text}%')
        )
    ).order_by(ServiceRequest.created_at.desc()).limit(10).all()
    
    total = len(items) + len(faqs) + len(requests)
    
    return render_template('directories/search.html', 
                         items=items, faqs=faqs, requests=requests,
                         query=query_text, total=total)
