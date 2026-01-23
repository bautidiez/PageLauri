from models import Producto, Categoria, Color, StockTalle, db
from sqlalchemy import or_, case
from extensions import limiter

class ProductService:
    @staticmethod
    def get_catalog(filters: dict, page: int = 1, page_size: int = 12):
        """
        Lógica centralizada para obtener productos con filtros complejos.
        """
        query = Producto.query
        
        # Filtro de activos por defecto
        if filters.get('activos') != 'false':
            query = query.filter_by(activo=True)
            
        # Búsqueda textual
        busqueda = filters.get('busqueda')
        if busqueda:
            search_term = f"%{busqueda}%"
            query = query.filter(or_(
                Producto.nombre.ilike(search_term),
                Producto.descripcion.ilike(search_term)
            ))
            
        # Categorías (Recursivo)
        categoria_id = filters.get('categoria_id')
        if categoria_id:
            def get_cat_ids(cat_id):
                ids = [int(cat_id)]
                subs = Categoria.query.filter_by(categoria_padre_id=cat_id).all()
                for s in subs:
                    ids.extend(get_cat_ids(s.id))
                return ids
            query = query.filter(Producto.categoria_id.in_(get_cat_ids(categoria_id)))
            
        # Otros filtros...
        if filters.get('destacados') == 'true':
            query = query.filter_by(destacado=True)
        
        # Filtro de ofertas: productos con precio_descuento O con promociones activas
        if filters.get('ofertas') == 'true':
            from datetime import datetime
            from models import PromocionProducto, promocion_productos_link, promocion_categorias_link
            ahora = datetime.utcnow()
            
            # Opción 1: Productos con precio_descuento
            tiene_descuento = (
                (Producto.precio_descuento.isnot(None)) &
                (Producto.precio_descuento > 0)
            )
            
            # Opción 2: Productos con promociones activas (directas)
            tiene_promo_directa = Producto.id.in_(
                db.session.query(promocion_productos_link.c.producto_id).join(
                    PromocionProducto,
                    PromocionProducto.id == promocion_productos_link.c.promocion_id
                ).filter(
                    PromocionProducto.activa == True,
                    PromocionProducto.fecha_inicio <= ahora,
                    PromocionProducto.fecha_fin >= ahora
                )
            )
            
            # Opción 3: Productos cuya categoría tiene promociones activas
            tiene_promo_categoria = Producto.categoria_id.in_(
                db.session.query(promocion_categorias_link.c.categoria_id).join(
                    PromocionProducto,
                    PromocionProducto.id == promocion_categorias_link.c.promocion_id
                ).filter(
                    PromocionProducto.activa == True,
                    PromocionProducto.fecha_inicio <= ahora,
                    PromocionProducto.fecha_fin >= ahora
                )
            )
            
            # Combinar todas las condiciones con OR
            query = query.filter(or_(tiene_descuento, tiene_promo_directa, tiene_promo_categoria))
            
        if filters.get('precio_min'):
            query = query.filter(Producto.precio_base >= float(filters['precio_min']))
        if filters.get('precio_max'):
            query = query.filter(Producto.precio_base <= float(filters['precio_max']))

            
        # Ordenamiento
        orden = filters.get('ordenar_por', 'nuevo')
        
        # Si hay búsqueda, priorizar por relevancia
        if busqueda and orden == 'nuevo':
            search_term = f"%{busqueda}%"
            query = query.order_by(
                case(
                    (Producto.nombre.ilike(search_term), 1),
                    (Producto.descripcion.ilike(search_term), 2),
                    else_=3
                ).asc(),
                Producto.created_at.desc()
            )
        elif orden == 'precio_asc':
            query = query.order_by(Producto.precio_base.asc())
        elif orden == 'precio_desc':
            query = query.order_by(Producto.precio_base.desc())
        elif orden == 'destacado':
            # Implementamos el orden de prioridad: 1. Destacados, 2. Ofertas, 3. Otros
            # Definimos qué es una "oferta" para el ordenamiento (misma lógica que el filtro de ofertas)
            from datetime import datetime
            from models import PromocionProducto, promocion_productos_link, promocion_categorias_link
            ahora = datetime.utcnow()
            
            # Opción 1: Productos con precio_descuento
            tiene_descuento = (Producto.precio_descuento > 0)
            
            # Opción 2: Productos con promociones activas (directas)
            tiene_promo_directa = Producto.id.in_(
                db.session.query(promocion_productos_link.c.producto_id).join(
                    PromocionProducto, PromocionProducto.id == promocion_productos_link.c.promocion_id
                ).filter(
                    PromocionProducto.activa == True,
                    PromocionProducto.fecha_inicio <= ahora,
                    PromocionProducto.fecha_fin >= ahora
                )
            )
            
            # Opción 3: Productos con promociones por categoría
            tiene_promo_categoria = Producto.categoria_id.in_(
                db.session.query(promocion_categorias_link.c.categoria_id).join(
                    PromocionProducto, PromocionProducto.id == promocion_categorias_link.c.promocion_id
                ).filter(
                    PromocionProducto.activa == True,
                    PromocionProducto.fecha_inicio <= ahora,
                    PromocionProducto.fecha_fin >= ahora
                )
            )

            is_offer = or_(tiene_descuento, tiene_promo_directa, tiene_promo_categoria)

            query = query.order_by(
                case(
                    (Producto.destacado == True, 1),
                    (is_offer, 2),
                    else_=3
                ).asc(),
                Producto.created_at.desc()
            )
        else:
            query = query.order_by(Producto.created_at.desc())
            
        return query.paginate(page=page, per_page=page_size, error_out=False)


    @staticmethod
    def get_by_id(product_id: int):
        return Producto.query.get(product_id)
