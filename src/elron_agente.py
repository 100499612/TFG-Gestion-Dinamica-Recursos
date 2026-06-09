import subprocess
import time
import re

USUARIO_ORIGEN = "elron"
USUARIO_DESTINO = "ibarrero"
HOST_DESTINO = "localhost"
PUERTO_TUNEL = "8022"

def escribir_log(lugar, origen, nuevos_ids):
    """Escribe el log súper limpio y seguro en Elron"""
    try:
        with open("/home/elron/EpiGraphFlexMPI/historial_global.log", "a") as f:
            f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ejecutando en {lugar}\n")
            f.write(f"Migrado desde: {origen}\n")
            ids_str = ", ".join(nuevos_ids) if nuevos_ids else "Desconocido"
            f.write(f"Tareas actuales en {lugar.capitalize()} (IDs): {ids_str}\n")
            f.write("-" * 50 + "\n")
    except Exception as e:
        print(f"Error log: {e}")


def monitorear_elron():
    print("Agente Multiclúster (Origen) Activo. Vigilando Elron...")
    intentos = 0
    umbral_intentos = 3
    escribir_log("elron", "Inicio manual", [])

    while True:
        resultado = subprocess.run(['squeue', '-u', USUARIO_ORIGEN, '-h'], capture_output=True, text=True)
        trabajos = resultado.stdout.strip().split('\n') if resultado.stdout.strip() else []
        num_trabajos = len(trabajos)
        print(f"[{time.strftime('%H:%M:%S')}] Servidor: Elron (Tocho) | Trabajos: {num_trabajos}")

        if num_trabajos <= 2:
            intentos += 1
            print(f"¡Baja carga detectada ({num_trabajos} trabajos)! Es ineficiente mantener Elron activo.\nConfirmando estabilidad ({intentos}/{umbral_intentos})...")

            if intentos >= umbral_intentos:
                print("Estabilidad confirmada. Iniciando protocolo de salto a TUCAN...")
                ejecutar_migracion_externa(num_trabajos)
                print("-" * 50)
                print("INFO: Hemos 'apagado' el clúster local (Elron) para ahorrar energía.")
                print("-" * 50)
                break
        else:
            if 0 < intentos < 3:
                intentos = 0
                print("Reiniciamos el controlador a 0 veces para evitar migraciones ineficientes")

        time.sleep(10)

def ejecutar_migracion_externa(cantidad_trabajos):
    with open("checkpoint.bin", "w") as f:
        f.write("1")
    time.sleep(15)

    print("Transfiriendo archivos de estado a Tucán mediante rsync...")
    # Rync ahora usa el túnel SSH por el puerto 8022
    resultado_rsync = subprocess.run([
        'rsync', '-avz', '--exclude', '*libxml*',
        '--exclude', 'epiGraph',
        '--exclude', '.*',
        '--exclude', 'slurm-*.out',
        '--exclude', 'cities/log/*',
        '--exclude', 'cities/v_stats*',
        '--exclude', 'output.old/*',
        '--exclude', 'output/*',
        '--exclude', 'logs/*',
        '--exclude', '*.o',
        '-e', f'ssh -p {PUERTO_TUNEL}',
        '/home/elron/EpiGraphFlexMPI/',
        f'{USUARIO_DESTINO}@{HOST_DESTINO}:/home/ibarrero/EpiGraphFlexMPI/'
    ])

    if resultado_rsync.returncode in [0, 24]:
        print("Sincronización exitosa. Procediendo con el salto...")

        comando_trabajos = (
            f"env -i bash -l -c 'cd /home/ibarrero/EpiGraphFlexMPI && "
            f"echo 0 > checkpoint.bin && "
            f"for i in $(seq 1 {cantidad_trabajos}); do "
            f"./TurboLanza_migrable.sh /home/ibarrero/FlexMPIDeveloper/run/nodefile2.dat; "
            f"sleep 1; "
            f"done'"
        )
        # Usamos ssh con el puerto 8022
        res = subprocess.run(['ssh', '-p', PUERTO_TUNEL, f'{USUARIO_DESTINO}@{HOST_DESTINO}', comando_trabajos], capture_output=True, text=True)

        nuevos_ids = re.findall(r"Submitted batch job (\d+)", res.stdout)
        escribir_log("tucan", "Elron", nuevos_ids)

        print("Resucitando el agente eficiente en Tucán...")
        comando_agente = "env -i bash -l -c 'cd /home/ibarrero/EpiGraphFlexMPI && nohup python3 agente_tucan.py > agente_tucan.log 2>&1 < /dev/null &'"
        subprocess.Popen(['ssh', '-p', PUERTO_TUNEL, f'{USUARIO_DESTINO}@{HOST_DESTINO}', comando_agente])
        time.sleep(2)

        print("Migración confirmada. Limpiando clúster origen (Elron)...")
        subprocess.run(['scancel', '-u', USUARIO_ORIGEN])
    else:
        print(f"¡Error en la sincronización (Código {resultado_rsync.returncode})! Migración abortada.")

if __name__ == "__main__":
    monitorear_elron()

