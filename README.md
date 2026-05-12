# CeSJ

Scraper de categorías + GitHub Action.

Extrae un árbol de categorías de un sitio web público,
lo encripta con AES-256-CBC y lo persiste en el repo.

## Cómo funciona

Un Action de GitHub corre semanalmente:

1. Scrapea las categorías del sitio
2. Compara con la versión anterior
3. Si hay cambios: encripta con AES-256 y pushea
4. Genera un reporte con el resumen

Si no hay cambios, no hace commit.

## Archivos

- `arbol-categorias.json.enc` — datos encriptados
- `reporte.txt` — resumen legible de la última corrida
- `extraer-arbol.py` — el scraper

## Local

Para desencriptar necesitás la key (no está en el repo).
Corre con `openssl`:

```
openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 \
  -in arbol-categorias.json.enc \
  -out arbol-categorias.json \
  -pass pass:"$KEY"
```
