# Gestión Dinámica de Recursos en Entornos Multiclúster Híbridos (HPC)

Repositorio oficial del Trabajo Fin de Grado (TFG). Contiene el código fuente y los scripts de un orquestador ligero diseñado para migrar dinámicamente simulaciones científicas (MPI) entre clústeres de alto rendimiento (arquitectura x86) y nodos de alta eficiencia energética (arquitectura ARM) en función de la demanda del sistema.

## Estructura del Proyecto

* **`/src/elron_agente.py`**: Agente orquestador principal (x86). Monitoriza la cola de Slurm, evalúa la carga mediante un algoritmo de histéresis y desencadena las migraciones.
* **`/src/agente_tucan.py`**: Agente de recepción en el nodo eficiente (ARM). Gestiona la reanudación de los trabajos y evalúa las condiciones de retorno al clúster principal.
* **`/scripts/TurboLanza_migrable.sh`**: Script principal de lanzamiento que adapta el entorno para permitir migraciones en caliente.
* **`/scripts/lanza_migrable.sh`**: *Wrapper* interno que adapta los comandos `mpiexec` dependiendo de la arquitectura en la que se despliegue.
* **`/multirm/`**: Utilidades integradas para gestionar los recursos distribuidos.

## Despliegue y Ejecución

### 1. Requisitos Previos (Autenticación)
Los nodos deben tener comunicación bidireccional automatizada mediante intercambio de claves SSH:

```bash
ssh-keygen -t rsa -b 4096
ssh-copy-id usuario@nodo_destino
```

### 2. Ejecución del Orquestador
Iniciar el agente en el clúster principal (ej. Elron). El script se mantendrá en escucha, monitorizando y gestionando las migraciones automáticamente:

```bash
python3 src/elron_agente.py
```

### 3. Lanzamiento de Trabajos
Para someter una simulación a la cola de Slurm bajo el control del orquestador, ejecutar desde la raíz del proyecto:

```bash
bash scripts/TurboLanza_migrable.sh
```

### 4. Monitorización
Las decisiones del agente y los saltos entre arquitecturas se registran en tiempo real en el historial de auditoría del nodo principal:

```bash
tail -f historial_global.log
```

## Integración con nuevos casos de uso
El orquestador es agnóstico a la aplicación subyacente. Para integrar simulaciones distintas a *EpiGraph*, la aplicación objetivo debe implementar un mecanismo de *checkpointing* a nivel de código fuente (generación periódica de archivos de estado `.dat` o similares), garantizando que el punto de guardado sea independiente de la arquitectura subyacente (x86/ARM).
