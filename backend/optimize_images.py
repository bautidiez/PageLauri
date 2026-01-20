"""
Script para optimizar imágenes de productos
Convierte JPG/PNG a WebP con compresión y redimensionamiento automático
"""
from PIL import Image
import os
from pathlib import Path

def convert_to_webp(input_path, output_path=None, quality=85, max_size=1200):
    """
    Convierte una imagen a formato WebP optimizado
    
    Args:
        input_path: Ruta de la imagen original
        output_path: Ruta de salida (opcional)
        quality: Calidad WebP (0-100, default 85)
        max_size: Tamaño máximo en píxeles (default 1200)
    """
    try:
        if output_path is None:
            output_path = str(Path(input_path).with_suffix('.webp'))
        
        # Abrir imagen
        img = Image.open(input_path)
        
        # Redimensionar si es muy grande
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            print(f"   📏 Redimensionado a {img.width}x{img.height}px")
        
        # Convertir a RGB si tiene alpha channel
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            img = background
        
        # Guardar como WebP
        img.save(output_path, 'WEBP', quality=quality, method=6)
        
        # Mostrar estadísticas
        original_size = os.path.getsize(input_path) / 1024
        new_size = os.path.getsize(output_path) / 1024
        saved_percent = ((original_size - new_size) / original_size) * 100
        
        print(f"✅ {Path(input_path).name}")
        print(f"   {original_size:.1f}KB → {new_size:.1f}KB (ahorro: {saved_percent:.1f}%)")
        
        return output_path
        
    except Exception as e:
        print(f"❌ Error procesando {input_path}: {e}")
        return None

def optimize_all_images(directory="static/uploads/productos", quality=85):
    """
    Optimiza todas las imágenes en un directorio
    
    Args:
        directory: Directorio a procesar
        quality: Calidad de compresión WebP
    """
    print(f"\n🔍 Buscando imágenes en: {directory}")
    
    uploads_dir = Path(directory)
    
    # Crear directorio si no existe
    if not uploads_dir.exists():
        print(f"⚠️  Directorio no encontrado: {directory}")
        print("   Creando directorio...")
        uploads_dir.mkdir(parents=True, exist_ok=True)
        return
    
    # Buscar imágenes
    image_extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
    images_found = []
    
    for ext in image_extensions:
        images_found.extend(list(uploads_dir.glob(f"*{ext}")))
        images_found.extend(list(uploads_dir.glob(f"**/*{ext}")))
    
    if not images_found:
        print("⚠️  No se encontraron imágenes para optimizar")
        return
    
    print(f"\n📸 Encontradas {len(images_found)} imágenes")
    print(f"🎯 Iniciando conversión a WebP (calidad: {quality})...\n")
    
    total_original = 0
    total_optimized = 0
    converted = 0
    
    for img_path in images_found:
        # Verificar si ya existe versión WebP
        webp_path = img_path.with_suffix('.webp')
        if webp_path.exists():
            print(f"⏭️  Ya existe: {img_path.name}")
            continue
        
        # Convertir
        result = convert_to_webp(str(img_path), str(webp_path), quality=quality)
        
        if result:
            converted += 1
            total_original += os.path.getsize(img_path) / 1024
            total_optimized += os.path.getsize(result) / 1024
        
        print()  # Línea en blanco
    
    # Resumen
    if converted > 0:
        total_saved = total_original - total_optimized
        percent_saved = (total_saved / total_original) * 100
        
        print("=" * 60)
        print("📊 RESUMEN")
        print("=" * 60)
        print(f"✅ Imágenes convertidas: {converted}")
        print(f"📦 Tamaño original total: {total_original:.1f}KB ({total_original/1024:.1f}MB)")
        print(f"📦 Tamaño optimizado total: {total_optimized:.1f}KB ({total_optimized/1024:.1f}MB)")
        print(f"💾 Espacio ahorrado: {total_saved:.1f}KB ({total_saved/1024:.1f}MB)")
        print(f"🎯 Reducción: {percent_saved:.1f}%")
        print("=" * 60)
    else:
        print("\n✨ Todas las imágenes ya están optimizadas")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 OPTIMIZADOR DE IMÁGENES - EL VESTUARIO")
    print("=" * 60)
    
    # Optimizar imágenes de productos
    optimize_all_images("static/uploads/productos", quality=85)
    
    # También optimizar assets si existen
    if Path("static/assets").exists():
        print("\n" + "=" * 60)
        optimize_all_images("static/assets", quality=90)
    
    print("\n✅ Proceso completado!")
    print("\n💡 SIGUIENTE PASO:")
    print("   Actualiza las referencias en el código para usar .webp en lugar de .jpg/.png")
