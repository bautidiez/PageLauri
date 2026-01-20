"""
Helper de paginación reutilizable para todos los endpoints admin
"""
from flask import request, jsonify

def paginate_query(query, serializer_func=None, default_page_size=50, max_page_size=200):
    """
    Helper para paginar cualquier query de SQLAlchemy
    
    Args:
        query: Query de SQLAlchemy
        serializer_func: Función para serializar cada item (opcional, usa to_dict() por defecto)
        default_page_size: Tamaño de página por defecto
        max_page_size: Tamaño máximo de página permitido
    
    Returns:
        JSON con items paginados y metadata
    """
    page = int(request.args.get("page", 1))
    page_size = min(int(request.args.get("page_size", default_page_size)), max_page_size)
    
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    
    if serializer_func:
        items = [serializer_func(item) for item in pagination.items]
    else:
        items = [item.to_dict() for item in pagination.items]
    
    return jsonify({
        "items": items,
        "total": pagination.total,
        "page": page,
        "page_size": page_size,
        "pages": pagination.pages
    })
