# 6. Código o implementación tecnológica

El modelo de transporte determina cuántas unidades enviar al mes desde cada una de las tres plantas a cada una de las seis ciudades para cubrir la demanda al menor costo.

## Entorno técnico y ejecución

La implementación se verificó en Windows con Python 3.13.5 y PuLP 4.3.1. PuLP construye el problema de programación lineal y el solucionador CBC calcula la asignación óptima. El módulo estándar `csv` escribe los resultados.

Desde la carpeta del proyecto, estos comandos de PowerShell instalan la dependencia y ejecutan las dos pruebas.

```powershell
py -3.13 -m pip install "pulp[cbc]==4.3.1"
py -3.13 main.py
```

## Repositorio de código

El código, los resultados exportados y la documentación están organizados en la rama `main`. [Repositorio del proyecto](https://github.com/viloriav999/proyect) · [Historial de commits](https://github.com/viloriav999/proyect/commits/main/)

## Del modelo matemático al código

### 1. Preparar la demanda

Las listas `capacidad` y `demanda_base` contienen unidades mensuales. La entrada `costos[i][j]` indica los USD que cuesta enviar una unidad desde la planta de la fila `i` a la ciudad de la columna `j`. La prueba base usa factor 1,0 y la segunda usa 1,15.

```python
demanda = [cantidad * factor for cantidad in demanda_base]
```

### 2. Representar los envíos y minimizar el costo

La variable continua `envio[i, j]` representa las unidades enviadas por una ruta. Hay 18 variables, una por cada combinación de planta y ciudad. El límite inferior cero impide envíos negativos. La función objetivo suma el costo de las 18 rutas en USD por mes.

```python
modelo = pulp.LpProblem("Transporte", pulp.LpMinimize)
origenes = range(len(plantas))
destinos = range(len(ciudades))
rutas = [(i, j) for i in origenes for j in destinos]
envio = modelo.add_variable_dicts("envio", rutas, lowBound=0)
modelo += pulp.lpSum(costos[i][j] * envio[i, j] for i, j in rutas)
```

### 3. Aplicar los límites del problema

Cada planta puede despachar hasta su capacidad. Cada ciudad debe recibir al menos su demanda. Ambas condiciones son obligatorias en las dos pruebas.

```python
for i in origenes:
    modelo += pulp.lpSum(envio[i, j] for j in destinos) <= capacidad[i], f"capacidad_{plantas[i]}"

for j in destinos:
    modelo += pulp.lpSum(envio[i, j] for i in origenes) >= demanda[j], f"demanda_{ciudades[j]}"
```

### 4. Resolver e interpretar el estado

```python
resultado = modelo.solve(pulp.COIN_CMD(msg=False))
estado = resultado.status_str
```

Con estado `Optimal`, el programa lee el costo de la función objetivo y las cantidades de cada ruta. En el escenario base calcula el ahorro respecto del costo mensual reportado de USD 28.600. Con estado `Infeasible`, informa el déficit de capacidad y deja vacíos los campos de costo y ahorro.

| Escenario | Demanda | Capacidad | Resultado mensual |
| --- | ---: | ---: | --- |
| Actual | 1.800 | 2.000 | Costo óptimo de USD 22.100 y ahorro de USD 6.500 (22,73 %) |
| Demanda +15 % | 2.070 | 2.000 | Faltan 70 unidades. Es imposible cubrir todas las ciudades con la capacidad disponible. |

### 5. Exportar la decisión

Cada ejecución muestra el resultado en la consola y actualiza dos archivos junto al programa, dentro de la carpeta `resultados`.

- [resumen.csv](resultados/resumen.csv) contiene una fila por escenario con estado, demanda, capacidad, faltante, costo mínimo y ahorro.
- [envios.csv](resultados/envios.csv) contiene las unidades y el costo unitario de las 18 rutas del escenario óptimo, incluidas las rutas con cero unidades. Por ejemplo, la planta P1 envía 300 unidades a C2 a USD 15 por unidad.
