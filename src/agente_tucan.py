import subprocess
import time
import re
import os

USUARIO_LOCAL = "ibarrero"
HOST_ORIGEN = "elron@localhost"
PUERTO_TUNEL = "9022"

UMBRAL_MAXIMO_TUCAN = 2


def escribir_log_remoto(lugar, origen, nuevos_ids):
    """Envía el log a Elron por SSH para que todo quede en un solo archivo"""
    ids_str = ", ".join(nuevos_ids) if nuevos_ids else "Desconocido"
    mensaje = f"\\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ejecutando en {lugar}\\nMigrado desde: {origen}\\nTareas actuales en {lugar.capitalize()} (IDs): {ids_str}\\n" + "-"*50
    subprocess.run(["ssh", "-p", PUERTO_TUNEL, HOST_ORIGEN, f"echo -e '{mensaje}' >> /home/elron/EpiGraphFlexMPI/historial_global.log"])


def monitorizar_tucan():
    print("Agente Multiclúster (Destino) Activo. Vigilando carga en Tucán...")

    while True:
        try:
            resultado = subprocess.run(["squeue", "-u", USUARIO_LOCAL, "-t", "R,PD,CF", "-h"], capture_output=True, text=True)
            trabajos = resultado.stdout.strip().split('\n') if resultado.stdout.strip() else []
            trabajos_en_tucan = len(trabajos)
        except Exception as e:
            print(f"[Error] No se pudo leer la cola local: {e}")
            trabajos_en_tucan = 0

        print(f"[{time.strftime('%H:%M:%S')}] Servidor: Tucán (Eficiente) | Trabajos: {trabajos_en_tucan}")

        if trabajos_en_tucan > UMBRAL_MAXIMO_TUCAN:
            print(f"¡Alta carga detectada ({trabajos_en_tucan} trabajos)! El clúster eficiente no da abasto.")
            print("Iniciando protocolo de retorno al clúster principal (Elron)...")
            ejecutar_retorno_a_elron(trabajos_en_tucan)
            print("-" * 50)
            print("INFO: Carga devuelta a Elron. Tucán vuelve a estar libre.")
            print("-" * 50)
            break 

        time.sleep(10)

def ejecutar_retorno_a_elron(cantidad_trabajos):
    with open("checkpoint.bin", "w") as f:
        f.write("1")
    time.sleep(15)

    resultado_jobs = subprocess.run(["squeue", "-u", USUARIO_LOCAL, "-h", "-o", "%i"], capture_output=True, text=True)
    job_ids = resultado_jobs.stdout.strip().split()

    print("[Tucan-Agent] Transfiriendo archivos de estado a Elron...")
    comando_rsync = [
        "rsync", "-avz", "--exclude", "*libxml*",
        '--exclude', 'epiGraph',
        "--exclude", ".*",
        "--exclude", "slurm-*.out",
        "--exclude", "cities/log/*",
        "--exclude", "cities/v_stats*",
        "--exclude", "output.old/*",
        '--exclude', 'output/*',
        "--exclude", "logs/*",
        "--exclude", "*.o",
        "-e", f"ssh -p {PUERTO_TUNEL}",
        "/home/ibarrero/EpiGraphFlexMPI/",
        f"{HOST_ORIGEN}:/home/elron/EpiGraphFlexMPI/"
    ]

    resultado_rsync = subprocess.run(comando_rsync)

    if resultado_rsync.returncode == 0:
        print("[Tucan-Agent] Sincronización exitosa. Delegando el control y limpieza a Elron...")
        script_slurm_elron = "/home/elron/EpiGraphFlexMPI/lanza.sh"

        comando_remoto = (
            f"bash -l -c 'cd /home/elron/EpiGraphFlexMPI && echo 0 > checkpoint.bin && "
            f"for i in $(seq 1 {cantidad_trabajos}); do sbatch -n 4 {script_slurm_elron} 4; sleep 1; done'"
        )
        print("[Tucan-Agent] Despertando a Elron y transfiriendo la ejecución...")
        res = subprocess.run(["ssh", "-p", PUERTO_TUNEL, HOST_ORIGEN, comando_remoto], capture_output=True, text=True)

        # ¡AQUÍ ESTÁ LA MAGIA QUE FALTABA PARA EL LOG!
        nuevos_ids = re.findall(r"Submitted batch job (\d+)", res.stdout)
        escribir_log_remoto("elron", "Tucan", nuevos_ids)

        # Arrancamos el agente de Elron de fondo
        subprocess.Popen(["ssh", "-p", PUERTO_TUNEL, HOST_ORIGEN, "bash -l -c 'cd /home/elron/EpiGraphFlexMPI && nohup python3 elron_agente.py > agente_elron.log 2>&1 < /dev/null &'"])

        time.sleep(3)

        print("[Tucan-Agent] Purgando procesos locales en Tucán...")
        subprocess.run(["scancel", "-u", USUARIO_LOCAL])
        subprocess.run(["pkill", "-9", "-u", USUARIO_LOCAL, "epiGraph"])
        subprocess.run(["pkill", "-9", "-u", USUARIO_LOCAL, "mpiexec"]) # Añadido el limpiador de OpenMPI por si acaso
        subprocess.run(["pkill", "-9", "-u", USUARIO_LOCAL, "orted"])   # Añadido el limpiador de zombies
        subprocess.run(["pkill", "-9", "-u", USUARIO_LOCAL, "sbatch"])
        print("[Tucan-Agent] Proceso de retorno completado. Abandono el clúster.")
        os._exit(0)
    else:
        print("[Tucan-Agent] ¡Error en el rsync! Retorno abortado para proteger datos.")

if __name__ == "__main__":
    monitorizar_tucan()

