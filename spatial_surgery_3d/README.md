# SPATIAL SURGERY – logo 3D

Modelo 3D generado desde `source/SPATIAL_SURGERY_01.ai` (vectores originales, sin retrazar).

- 15 piezas independientes: `00_Icono` + cada letra (`01_S` … `14_Y`)
- Grosor: 5 mm · Bisel redondeado: 0.4 mm en letras, 0.2 mm en el ícono (hacia dentro, el contorno exterior respeta el diseño original)
- Escala: 1 pt del .ai = 1 mm → logo de ~378 × 79 mm (letras de 22.5 mm de alto)
- Color: naranja del logo (RGB 249, 157, 42)

## Archivos (`output/`)
| Archivo | Uso |
|---|---|
| `SPATIAL_SURGERY.obj` + `.mtl` | Malla con cada letra como objeto separado (unidades: mm) |
| `SPATIAL_SURGERY_3D.blend` | Escena Blender: curvas editables (bisel/grosor ajustables) + mallas, cámara y luces |
| `SPATIAL_SURGERY.fbx` / `.glb` | Otros formatos (el .glb está en metros reales) |
| `stl/*.stl` | Una pieza por archivo, listas para impresión 3D (mm) |
| `SPATIAL_SURGERY_completo.stl` | Todas las piezas en un solo STL |
| `preview.png` | Render de vista previa |

## Regenerar
```
pip install bpy pymupdf
python3 build_logo_3d.py
```
Parámetros (`THICKNESS`, `BEVEL`, `BEVEL_ICON`) al inicio del script.
