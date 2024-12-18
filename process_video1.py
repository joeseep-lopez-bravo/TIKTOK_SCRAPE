import os
import asyncio
import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from fake_useragent import UserAgent
import time
import logging
from db_connection_tk import DatabaseConnection

class video_process:
    def __init__(self):
        user_agent = UserAgent(platforms='pc')
        chrome_options = Options()

        self.download_dir = os.path.join(os.getcwd(), "videos_descargados")  # Carpeta de descargas
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)  # Crea la carpeta si no existe

        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": self.download_dir,  # Carpeta de descarga
            "download.prompt_for_download": False,           # No pregunta antes de descargar
            "download.directory_upgrade": True,              # Reemplaza si ya existe
            "safebrowsing.enabled": True                     # Desactiva advertencias de seguridad
        })
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument(f'user-agent={user_agent.random}')
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        self.page_link = 'https://snaptik.app/es2'

        self.conexion = DatabaseConnection()
        self.conexion.crear_conexion()

        self.ultimo_id_video_file = "ultimo_id_video.txt"  # Archivo para guardar el último ID procesado

    def leer_ultimo_id_video(self):
        """Leer el último ID desde el archivo."""
        if not os.path.exists(self.ultimo_id_video_file):
            with open(self.ultimo_id_video_file, "w") as f:
                f.write("0")  # Inicializa el archivo con 0 si no existe
            return 0
        with open(self.ultimo_id_video_file, "r") as f:
            return int(f.read().strip())

    def guardar_ultimo_id_video(self, ultimo_id_video):
        """Guardar el último ID procesado en el archivo."""
        with open(self.ultimo_id_video_file, "w") as f:
            f.write(str(ultimo_id_video))

    def generador_enlaces(self):
        try:
            ultimo_id_video = self.leer_ultimo_id_video()  # Leer el último ID procesado
            with self.conexion.connection.cursor() as cursor:
                consulta = "SELECT url, id, publicacion_id FROM video WHERE id > %s"
                cursor.execute(consulta, (ultimo_id_video,))
                for resultado in cursor:
                    yield resultado  # Devuelve cada resultado (url, id, publicacion_id) de uno en uno
        except psycopg2.Error as e:
            logging.error(f"Error en la base de datos con la tabla videos: {e}")
        except Exception as e:
            logging.error(f"Algo está pasando al generar enlaces: {e}")

    async def esperar_archivo(self, nombre_carpeta, tiempo_espera):
        tiempo_transcurrido = 0
        archivos_antes = set(os.listdir(nombre_carpeta))
        while tiempo_transcurrido < tiempo_espera:
            archivos_despues = set(os.listdir(nombre_carpeta))
            nuevos_archivos = archivos_despues - archivos_antes  # Detectar archivos nuevos
            for archivo in nuevos_archivos:
                if archivo.endswith('.mp4'):  # Verificar que sea un archivo de video
                    return archivo  # Devolver el nombre del archivo encontrado
            await asyncio.sleep(1)
            tiempo_transcurrido += 1
        return None 
    def configurar_logger(self):
        # Configuración básica del logger
        logging.basicConfig(filename='Logs_Obtener_videos.log',  # Archivo donde se guardarán los logs
                            level=logging.INFO,     # Nivel de registro, en este caso errores
                            format='%(asctime)s - %(levelname)s - %(message)s',  # Formato del log
                            datefmt='%Y-%m-%d %H:%M:%S')  # Formato de la fecha y hora      
    async def obtener_video(self):
        try:
            self.configurar_logger()
            ultimo_id_video_procesado = self.leer_ultimo_id_video()
            for url, video_id, publicacion_id in self.generador_enlaces():
                if "photo" in url:
                    print(f"URL contiene 'photo', omitiendo video con ID {video_id}.")
                else:
                    if url:
                        self.driver.get(self.page_link)
                        time.sleep(2)
                        try:
                            close_modal = WebDriverWait(self.driver, 15).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "button.modal-close.is-large"))
                            )               
                            close_modal.click()
                        except Exception as e:
                            print(f"No se encontró el modal para cerrar")    

                        try:
                            input_enlace = self.driver.find_element(By.CSS_SELECTOR, "input[name ='url']")
                            input_enlace.send_keys(url)

                            button_to_video = WebDriverWait(self.driver, 15).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit']"))
                                )
                            button_to_video.click()
                            time.sleep(2)
                            button_to_get = WebDriverWait(self.driver, 15).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.button.download-file"))
                                )
                            contador = 1
                            time.sleep(2)

                            download_url = button_to_get.get_attribute('href')
                            time.sleep(2)
                            self.driver.execute_script("window.open(arguments[0]);", download_url)
                            
                            # Espera la descarga del archivo y cambia su nombre si es necesario
                            archivo_descargado = await self.esperar_archivo("videos_descargados", 60)
                            if archivo_descargado:
                                self.cambiar_nombre(archivo_descargado, video_id, publicacion_id)
                                contador += 1  # Incrementa el contador para el próximo video
                            else:
                                print("No se encontró el archivo después del tiempo de espera.")
                            time.sleep(5)
                        except Exception as e:
                            print(f"Error al procesar el video: {e}")

            # Independientemente de si se omitió o no, actualizamos el último ID procesado
            ultimo_id_video_procesado = video_id  # Actualiza el último ID procesado

            self.guardar_ultimo_id_video(ultimo_id_video_procesado)  # Guarda el último ID procesado
        except Exception as e:
            logging.error(f"Error al procesar los videos o no hay videos nuevos: {e}")

    def cambiar_nombre(self, archivo_descargado, video_id, publicacion_id, ):
        download_dir = "videos_descargados"
        nuevo_nombre = f"{video_id}_{publicacion_id}.mp4"
        nuevo_archivo = os.path.join(download_dir, nuevo_nombre)
        # Evitar conflictos de nombres
        os.rename(os.path.join(download_dir, archivo_descargado), nuevo_archivo)
        print(f"Video descargado y renombrado a: {nuevo_nombre}")

    def cerrar_conexion(self):
        try:
            self.conexion.connection.close()
            self.driver.quit()
            print("Conexión cerrada y navegador cerrado.")
        except Exception as e:
            logging.error(f"Error al cerrar la conexión o el navegador: {e}")

async def main():
    
    video_extractor = video_process()
    await video_extractor.obtener_video()
    video_extractor.cerrar_conexion()

if __name__ == "__main__":
    asyncio.run(main())
