from flask import Blueprint, request, jsonify
from flask_login import login_required
from app import db
from app.models.directory import DirectoryCategory, DirectoryItem, FAQ
from app.models.request import ServiceRequest

api_bp = Blueprint('api', __name__)


@api_bp.route('/directories/categories')
@login_required
def get_categories():
    """Получение всех категорий."""
    categories = DirectoryCategory.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'description': c.description,
        'parent_id': c.parent_id,
        'items_count': c.items.count()
    } for c in categories])


@api_bp.route('/directories/items')
@login_required
def get_directory_items():
    """Получение элементов справочника с поиском."""
    search = request.args.get('q', '').strip()
    category_id = request.args.get('category_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
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
    
    items = query.order_by(DirectoryItem.priority.desc())\
        .paginate(page=page, per_page=per_page)
    
    return jsonify({
        'items': [{
            'id': item.id,
            'title': item.title,
            'content': item.content[:200] + '...' if len(item.content) > 200 else item.content,
            'category': item.category.name if item.category else '',
            'priority': item.priority,
            'views': item.views_count
        } for item in items.items],
        'total': items.total,
        'page': items.page,
        'pages': items.pages
    })


@api_bp.route('/faq')
@login_required
def get_faq():
    """Получение списка FAQ."""
    faqs = FAQ.query.filter_by(is_active=True).order_by(FAQ.views_count.desc()).all()
    return jsonify([{
        'id': f.id,
        'question': f.question,
        'answer': f.answer,
        'views': f.views_count
    } for f in faqs])


@api_bp.route('/faq/search')
@login_required
def search_faq():
    """Поиск в FAQ."""
    query_text = request.args.get('q', '').strip()
    
    if not query_text:
        return jsonify([])
    
    faqs = FAQ.query.filter(
        FAQ.is_active == True,
        db.or_(
            FAQ.question.ilike(f'%{query_text}%'),
            FAQ.answer.ilike(f'%{query_text}%')
        )
    ).limit(10).all()
    
    return jsonify([{
        'id': f.id,
        'question': f.question,
        'answer': f.answer
    } for f in faqs])


@api_bp.route('/requests/<int:request_id>/comments')
@login_required
def get_request_comments(request_id):
    """Получение комментариев запроса."""
    from app.models.request import RequestComment
    comments = RequestComment.query.filter_by(request_id=request_id)\
        .order_by(RequestComment.created_at).all()
    
    return jsonify([{
        'id': c.id,
        'text': c.text,
        'is_internal': c.is_internal,
        'user': c.user.full_name or c.user.username,
        'created_at': c.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for c in comments])
