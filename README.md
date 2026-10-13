# Hidroeléctricas de CELEC

Visualizador de caudales, niveles (cotas) y producción de las centrales hidroeléctricas de CELEC: Mazar, Molino (embalse de Amaluza), Sopladora, Minas San Francisco, Agoyán, Manduriacu y Coca Codo Sinclair, además del caudal de la cuenca del río Paute. Vista diaria (por hora) y mensual (por día).

Fuente: https://generacioncsr.celec.gob.ec/graficasproduccionCELEC/index.html

## Archivos

- `index.html`: el visualizador. Se abre en Hidrología y tiene un selector para pasar a Producción.
- `data/hidrologia-diario.csv`, `data/hidrologia-mensual.csv`, `data/produccion-diario.csv`, `data/produccion-mensual.csv`: los datos, con el mismo formato del botón "Descargar CSV" de CELEC.
- `scripts/actualizar.py`: descarga los datos del servicio de CELEC y reescribe los cuatro CSV.
- `.github/workflows/actualizar.yml`: ejecuta el script cada hora en GitHub y guarda los cambios.

## Insertar en la nota

```html
<iframe src="https://davidmunoz-create.github.io/hidroelectricamazar/" title="Caudales, niveles y producción de las hidroeléctricas de CELEC" width="100%" height="1150" style="border:0;" loading="lazy"></iframe>
```

Opciones en la dirección (se combinan con `&`):

- `?central=maz`: central que aparece primero. Valores: `paute`, `maz`, `mol`, `sop`, `msf`, `ago`, `man`, `ccs`, y `total` (solo en Producción).
- `?vista=produccion`: abre en Producción.
- `?periodo=mensual`: abre en la vista mensual.

Ejemplo: `?vista=produccion&central=total` abre la producción de todas las centrales.

## Actualización

**Automática.** El flujo de GitHub Actions corre cada hora. En la pestaña Actions se ve cada ejecución y está el botón "Run workflow" para correrlo a mano.

**Manual.** En la página de CELEC, elegir Tipo (Hidrología o Producción) y Periodo (Diaria o Mensual), pulsar "Descargar CSV" y subir el archivo a la carpeta `data/` con el nombre que corresponda:

| En CELEC | Nombre en `data/` |
|---|---|
| Hidrología, Diaria | `hidrologia-diario.csv` |
| Hidrología, Mensual | `hidrologia-mensual.csv` |
| Producción, Diaria | `produccion-diario.csv` |
| Producción, Mensual | `produccion-mensual.csv` |

**Desde una computadora.** Con Python instalado: `python scripts/actualizar.py` y luego subir los CSV. Se puede indicar una fecha: `python scripts/actualizar.py 2026-10-13`.

## Notas sobre los datos

- CELEC registra 0 o deja vacío cuando no hay dato. Una cota en 0 se muestra como "sin dato". Una energía en 0 dentro de una hora con datos es real: la central no generó.
- En el mensual de hidrología, el caudal es el promedio del día y la cota es el valor al cierre del día (hora 24).
- Mazar muestra los metros sobre su cota crítica (2 115 m s. n. m.) y un botón para marcarla en el gráfico. Amaluza, Sopladora y Minas San Francisco muestran su posición en el rango de cota que publica CELEC. Agoyán, Manduriacu y Coca Codo Sinclair muestran el cambio de cota en el periodo.
- El total mensual de producción se muestra desde el primer día con datos de las siete centrales.
