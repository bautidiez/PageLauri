"""
Sistema de caché simple en memoria con TTL (Time To Live)
"""
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Optional
import hashlib
import json

class CacheEntry:
    """Entrada de caché con valor y tiempo de expiración"""
    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.expiry = datetime.now() + timedelta(seconds=ttl_seconds)
    
    def is_expired(self) -> bool:
        """Verifica si la entrada ha expirado"""
        return datetime.now() > self.expiry

class SimpleCache:
    """Sistema de caché simple en memoria con TTL"""
    def __init__(self):
        self._cache = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del caché si existe y no ha expirado"""
        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired():
                return entry.value
            else:
                # Eliminar entrada expirada
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Guarda un valor en el caché con TTL (default 5 minutos)"""
        self._cache[key] = CacheEntry(value, ttl_seconds)
    
    def delete(self, key: str):
        """Elimina una entrada del caché"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        """Limpia todo el caché"""
        self._cache.clear()
    
    def clear_pattern(self, pattern: str):
        """Elimina todas las entradas que contengan el patrón"""
        keys_to_delete = [key for key in self._cache.keys() if pattern in key]
        for key in keys_to_delete:
            del self._cache[key]

# Instancia global del caché
cache = SimpleCache()

def make_cache_key(func_name: str, *args, **kwargs) -> str:
    """Generar una clave de caché basada en nombre de función, argumentos y parámetros de búsqueda de Flask"""
    from flask import request
    
    # Capturar argumentos de la función
    data = {
        'args': args,
        'kwargs': {k: v for k, v in kwargs.items() if k != 'self'}
    }
    
    # Si hay un contexto de petición de Flask, incluir los parámetros de búsqueda (query params)
    try:
        if request:
            data['query_params'] = dict(request.args)
    except RuntimeError:
        # Fuera de un contexto de petición (ej: scripts, tests)
        pass
        
    args_str = json.dumps(data, sort_keys=True, default=str)
    
    # Generar hash para acortar la clave
    args_hash = hashlib.md5(args_str.encode()).hexdigest()[:12]
    return f"{func_name}:{args_hash}"

def cached(ttl_seconds: int = 300):
    """
    Decorador para cachear el resultado de una función
    
    Args:
        ttl_seconds: Tiempo de vida del caché en segundos (default: 300 = 5 minutos)
    
    Uso:
        @cached(ttl_seconds=600)
        def get_productos():
            return Producto.query.all()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave de caché
            cache_key = make_cache_key(func.__name__, *args, **kwargs)
            
            # Intentar obtener del caché
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Si no está en caché, ejecutar función
            result = func(*args, **kwargs)
            
            # Guardar en caché
            cache.set(cache_key, result, ttl_seconds)
            
            return result
        return wrapper
    return decorator

def invalidate_cache(pattern: Optional[str] = None, key: Optional[str] = None):
    """
    Invalida el caché
    
    Args:
        pattern: Patrón para eliminar entradas que lo contengan
        key: Clave específica para eliminar
    
    Uso:
        # Eliminar todo el caché de productos
        invalidate_cache(pattern='get_productos')
        
        # Eliminar una clave específica
        invalidate_cache(key='get_producto:abc123')
    """
    if pattern:
        cache.clear_pattern(pattern)
    elif key:
        cache.delete(key)
    else:
        cache.clear()
