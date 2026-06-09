# Gestión Dinámica de Recursos en Entornos Multiclúster Híbridos (HPC)

Este repositorio contiene el código y los scripts desarrollados para mi Trabajo de Fin de Grado (TFG). 

En resumen, el proyecto es un sistema automático que mueve simulaciones científicas (EpiGraph/FlexMPI) entre servidores potentes (x86) y placas de bajo consumo (ARM). El sistema vigila la carga de trabajo en tiempo real: si hay poco que hacer, manda la simulación al nodo eficiente para ahorrar energía; si entra mucha carga, devuelve el trabajo al servidor principal para no perder rendimiento.

## Estructura del Proyecto

El código se organiza en las siguientes carpetas:

* **`src/` (Código Principal)**:
  * `elron_agente.py`: Es el "cerebro" en el servidor principal (*Elron*, x86). Vigila la cola de Slurm y decide cuándo mover los procesos al nodo de ahorro.
  * `agente_tucan.py`: Es el agente que corre en el nodo de bajo consumo (*Tucán*, ARM). Recibe los trabajos, los ejecuta y los devuelve automáticamente al servidor principal si se queda sin recursos.
* **`scripts/` (Lanzamiento de Trabajos)**:
  * `TurboLanza_migrable.sh`: Script principal que debes usar para arrancar las simulaciones de forma compatible con la migración.
  * `lanza_migrable.sh`: Script interno que adapta los comandos de MPI (`mpiexec`) dependiendo de la máquina en la que esté corriendo.
* **`multirm/`**: Utilidades integradas para gestionar los recursos distribuidos entre los distintos nodos.
* **`scripts_de_prueba/`**: Scripts básicos (como `test_slurm.py`) para comprobar que la comunicación local con Slurm funciona bien antes de poner a correr el sistema real.

## Despliegue y Ejecución

Arrancar el sistema es muy sencillo y se controla al 100% desde el servidor principal.

### 1. Configuración Previa
Antes de arrancar, las máquinas tienen que poder comunicarse por red sin pedir contraseña. Para ello, genera y copia las claves SSH desde el servidor principal hacia el nodo de reserva ejecutando esto:

```bash
ssh-keygen -t rsa -b 4096
ssh-copy-id usuario@tucan
```

### 2. Ejecución del Agente Principal
No hace falta ir máquina por máquina configurando cosas. Solo tienes que arrancar el script en el clúster principal (*Elron*). Este script se quedará escuchando y se encargará de contactar y mover las tareas a *Tucán* de forma automática cuando toque:

```bash
python3 src/elron_agente.py
```

### 3. Envío del Trabajo a Slurm
Para lanzar la simulación y que el agente la vigile para poder migrarla, ejecuta esto desde la raíz del proyecto:

```bash
bash scripts/TurboLanza_migrable.sh
```

### 4. Monitorización e Historial (Logs)
Mientras el sistema funciona, los agentes se comunican por red y guardan todos los saltos y migraciones en un único archivo en el servidor principal. Puedes consultar este "diario" en cualquier momento para ver por dónde va la simulación:

```bash
cat EpiGraph/historial_global.log
```
*(Sugerencia: usa `tail -f EpiGraph/historial_global.log` si quieres verlo en directo).*

## Notas sobre los Nodos
Si echas en falta los archivos `nodefile.dat` o `nodefile2.dat`, es porque están en el `.gitignore`. El sistema ya no necesita listas fijas, sino que averigua la topología sobre la marcha preguntándole a Slurm qué nodos nos ha asignado:

```bash
scontrol show hostnames $SLURM_JOB_NODELIST
```
