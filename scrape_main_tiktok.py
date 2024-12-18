import subprocess
import time
import argparse
import logging
# Variables para almacenar los subprocesos en ejecución
processes = []

def ejecutar_script(script_name):
    """Ejecuta un script y espera a que termine."""
    logging.info(f"Ejecutando script {script_name}...")
    process = subprocess.Popen(["python", script_name])
    processes.append(process)
    process.wait()  # Espera a que el script termine antes de continuar


def ejecutar_login_topic():
    logging.info("Ejecutando script de tema...")
    process1 = subprocess.Popen(["python", "scrape_topic_tk_full.py"])
    process1.wait()  # Espera a que scrape_topic_tk_full.py termine

    logging.info("Ejecutando script de video...")
    process2 = subprocess.Popen(["python", "process_video1.py"])
    process2.wait()  # Espera a que process_video1.py termine

def ejecutar_login_perfil():
    logging.info("Ejecutando script de tema...")
    process1 = subprocess.Popen(["python", "scrape_perfil_tk_full.py"])
    process1.wait()  # Espera a que scrape_topic_tk_full.py termine

    logging.info("Ejecutando script de video...")
    process2 = subprocess.Popen(["python", "process_video1.py"])
    process2.wait()  # Espera a que process_video1.py termine    

def ejecutar_topic():
    logging.info("Ejecutando script de tema...")
    process1 = subprocess.Popen(["python", "scrape_topic_tk.py"])
    process1.wait()  # Espera a que scrape_topic_tk_full.py termine

    logging.info("Ejecutando script de video...")
    process2 = subprocess.Popen(["python", "process_video1.py"])
    process2.wait()  # Espera a que process_video1.py termine

def ejecutar_perfil():
    logging.info("Ejecutando script de tema...")
    process1 = subprocess.Popen(["python", "scrape_perfil_tk.py"])
    process1.wait()  # Espera a que scrape_topic_tk_full.py termine

    logging.info("Ejecutando script de video...")
    process2 = subprocess.Popen(["python", "process_video1.py"])
    process2.wait()  # Espera a que process_video1.py termine

# Función para cancelar todos los scripts en ejecución
def cancelar_todos_los_scripts():
    for process in processes:
        if process.poll() is None:  # Verifica si el proceso sigue en ejecución
            logging.info("Cancelando script...")
            process.terminate()
    processes.clear()  # Limpia la lista de procesos
def configurar_logger():
    # Configuración básica del logger
    logging.basicConfig(filename='Logs_SCRAPE_tiktok_MAIN.log',  # Archivo donde se guardarán los logs
                        level=logging.INFO,     # Nivel de registro, en este caso errores
                        format='%(asctime)s - %(levelname)s - %(message)s',  # Formato del log
                        datefmt='%Y-%m-%d %H:%M:%S')  # Formato de la fecha y hora      
# Función principal para parsear los argumentos y ejecutar los scripts
def main():
    # Crear el parser para los argumentos
    parser = argparse.ArgumentParser(description="Ejecutar scripts específicos.")
    parser.add_argument(
        '--funcion_ejecutar',
        choices=['perfil_login', 'busqueda_login', 'perfil', 'busqueda',],
        help="Función que deseas ejecutar.",
        required=True
    )
    args = parser.parse_args()

    # Ejecutar según el valor del argumento
    if args.funcion_ejecutar == 'perfil_login':
        ejecutar_login_perfil()
        logging.info("Scripts de perfil login ejecutados.")
    elif args.funcion_ejecutar == 'busqueda_login':
        ejecutar_login_topic()
        logging.info("Scripts de búsqueda login ejecutados.")
    elif args.funcion_ejecutar == 'perfil':
        ejecutar_perfil()
        logging.info("Scripts de perfil ejecutados.")
    elif args.funcion_ejecutar == 'busqueda':
        ejecutar_topic()
        logging.info("Scripts de búsqueda ejecutados.") 

# Ejecutar el script principal
if __name__ == "__main__":
    try:
        configurar_logger()
        main()
    except KeyboardInterrupt:
        logging.error("Cancelando todos los scripts...")
        cancelar_todos_los_scripts()
