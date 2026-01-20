# 📋 Instrucciones para Nueva Estructura de Categorías

## 🔄 CAMBIOS IMPLEMENTADOS

### ✅ Cambio 1: Ofertas
- **ANTES:** Ofertas era una categoría principal
- **AHORA:** Ofertas es una subcategoría tanto de Remeras como de Shorts

### ✅ Cambio 2: Selecciones  
- **ANTES:** Selecciones aparecía en Retro, Temporada 24/25 y Temporada 25/26
- **AHORA:** Selecciones solo aparece en Retro

### ✅ Cambio 3: Brasileirão
- **NUEVO:** Se agregó Brasileirão como liga en Retro, Temporada 24/25 y Temporada 25/26

---

## 📊 Estructura Resultante

### Categorías Principales (2):
- **Remeras**
- **Shorts**

### Remeras → Subcategorías (8):
1. Conjuntos
2. Entrenamiento
3. Mundial 2026
4. Ofertas
5. Retro
6. Selección 24/25
7. Temporada 24/25
8. Temporada 25/26

### Shorts → Subcategorías (2):
1. Entrenamiento
2. Ofertas

### Sub-subcategorías (Ligas):

**Retro (8 ligas):**
- Brasileirão
- Bundesliga
- Futbol Argentino
- La Liga
- Premier League
- Resto del mundo
- Selecciones ⭐
- Serie A

**Temporada 24/25 (7 ligas):**
- Brasileirão
- Bundesliga
- Futbol Argentino
- La Liga
- Premier League
- Resto del mundo
- Serie A

**Temporada 25/26 (7 ligas):**
- Brasileirão
- Bundesliga
- Futbol Argentino
- La Liga
- Premier League
- Resto del mundo
- Serie A

---

## 🚀 Ejecutar Nueva Estructura

### Paso 1: Activar entorno virtual

```powershell
cd C:\Bau\PagLauri\backend
.\venv\Scripts\Activate.ps1
```

### Paso 2: Ejecutar script de nueva estructura

```powershell
python crear_categorias_nueva_estructura.py
```

---

## 📈 Totales

- **Categorías Principales:** 2
- **Subcategorías Nivel 1:** 10 (8 en Remeras + 2 en Shorts)
- **Sub-subcategorías Nivel 2:** 22 (8 en Retro + 7 en Temp 24/25 + 7 en Temp 25/26)
- **TOTAL:** 34 categorías

---

## ⚠️ Importante

> **Backup de Base de Datos**
> 
> Antes de ejecutar, haz backup:
> ```powershell
> copy C:\Bau\PagLauri\backend\instance\elvestuario.db C:\Bau\PagLauri\backend\instance\elvestuario.db.backup
> ```

> **Productos Existentes**
> 
> Los productos asignados a categorías modificadas necesitarán ser reasignados manualmente desde el panel de administración.
