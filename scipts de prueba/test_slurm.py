import subprocess

def check_slurm():
    try:
        # Ejecutamos el comando sinfo para ver el estado de los nodos
        resultado = subprocess.run(['sinfo'], capture_output=True, text=True)
        print("Salida de Slurm:")
        print(resultado.stdout)
    except FileNotFoundError:
        print("Error: No se encuentra el comando 'sinfo'. ¿Estás en el clúster?")

if __name__ == "__main__":
    check_slurm()