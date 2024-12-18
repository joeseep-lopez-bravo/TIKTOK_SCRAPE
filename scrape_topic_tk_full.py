from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
#from selenium.webdriver.chrome.service import Service
#from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
from tiktok_captcha_solver import SeleniumSolver
import undetected_chromedriver as uc
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from fake_useragent import UserAgent
from seleniumwire import webdriver
from datetime import datetime, timedelta
import time
import threading
from db_connection_tk import DatabaseConnection
import psycopg2
import random
import logging
import configparser
class Scrape_topic_tk():
    
    # Configurar logging
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.stop_event = None
        self.captcha_thread = None
        # Crear driver con Selenium Wire
        self.driver = uc.Chrome(
            options=chrome_options,
            headless=False
        )
            
        
        stealth(self.driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )

        self.config = configparser.ConfigParser()
        self.config.read('credentials.conf')
        self.credentials = self.get_credentials()

        self.config.read('api_keys.conf')
        self.api_key_captcha = self.config.get('CAPTCHA_SOLVER', 'api_key', fallback=None)

        self.sadcaptcha = SeleniumSolver(
            self.driver,
            self.api_key_captcha,
            mouse_step_size=1,  # Ajustar velocidad del mouse
            mouse_step_delay_ms=10  # Ajustar delay del mouse
        )

# Si la clave no se encuentra, 'fallback' le dará un valor por defecto (None)
        if self.api_key_captcha is None:
            raise ValueError("La clave 'api_key' no está definida en la sección 'CAPTCHA_SOLVER' de 'api_keys.conf'")
        
        self.selectors_boton_busqueda= [
                               'div > button[ aria-label="Buscar"]','button[ data-e2e="login-button"]']
        
        self.selectors_busqueda= [
                               'div.css-kdngec-DivSearchContainer.e1lvfea05 form input[placeholder="Buscar"]','input[placeholder="Buscar"]']
        self.selectors_divs= ["div[mode='search-video-list']",
                              "div[data-e2e='explore-item-list']"]
        self.selectors_divs_one= ["div.css-1soki6-DivItemContainerForSearch.e19c29qe19",
                              "div.css-x6y88p-DivItemContainerV2.e19c29qe17"]
        self.conexion = DatabaseConnection()
        self.conexion.crear_conexion()
    def get_credentials(self):
        config = configparser.ConfigParser()
        config.read('credentials.conf')
        credentials = []
        for key in config['DEFAULT']:
            if key.startswith('emailkey'):
                num = key.replace('emailkey', '')
                email = config.get('DEFAULT', f'emailkey{num}')
                password = config.get('DEFAULT', f'passwordkey{num}')
                credentials.append((email, password))
        return credentials
    def random_time(self,min_seconds, max_seconds):
        time.sleep(random.uniform(min_seconds, max_seconds))
    def obtener_comentario(self,driver):
        try:
            time.sleep(1)  # Espera inicial de 1 segundo
            
            feed_div = WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div.css-1qp5gj2-DivCommentListContainer.ekjxngi3"))
            )
            # Espera hasta que los elementos dentro de feed_div estén presentes
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.css-1i7ohvi-DivCommentItemContainer.eo72wou0"))
            )
            # Buscar los elementos dentro de feed_div
            divs = feed_div.find_elements(By.CSS_SELECTOR, "div.css-1i7ohvi-DivCommentItemContainer.eo72wou0")
            logging.info(f"Cantidad total de comentarios: {len(divs)}")
            return divs
        except NoSuchElementException as e:
            logging.error(f"Error: Could not locate the 'feed_div' or 'subelelementos' elements: {e}")
        except TimeoutException as e:
            logging.error(f"Error: Timeout waiting for elements: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in obtener_posts: {e}")
            return [] 
    def configurar_logger(self):
        # Configuración básica del logger
        logging.basicConfig(filename='Logs_Scraper_Busqueda_Login_TikTok.log',  # Archivo donde se guardarán los logs
                            level=logging.INFO,     # Nivel de registro, en este caso errores
                            format='%(asctime)s - %(levelname)s - %(message)s',  # Formato del log
                            datefmt='%Y-%m-%d %H:%M:%S')  # Formato de la fecha y hora  
    def wait_for_element_visible(self, by, selector, timeout):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, selector))
            )
        except Exception as e:
            logging.error(f"Error esperando elemento {selector}: {e}")
            return None    
    def detectar_captcha(self, driver):
        try:
            captcha = driver.find_element(By.CSS_SELECTOR, 'div.TUXModal.captcha-verify-container')  # Reemplaza con el selector correcto
            return True
        except Exception:
            return False
    def monitor_captcha(self, driver, stop_event):
        while not stop_event.is_set():
            try:
                if self.detectar_captcha(driver):
                    logging.info("Captcha detectado. Intentando resolver...")
                    self.resolver_captcha(driver)
                else:
                    logging.info("No se detecto captcha")
            except Exception as e:
                logging.error(f"Error al monitorear captcha: {e}")
            finally:
                time.sleep(1) 
    def resolver_captcha(self,driver):
        #self.sadcaptcha.solve_captcha_if_present()
        logging.info("Captcha resuelto")
    def find_search_input(self,driver):
        for selector in self.selectors_busqueda:
            try:
                search_input = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                if search_input:
                    return search_input  # Devuelve si se encuentra el elemento
            except Exception as e:
                logging.error(f"Error al tratar de obtener o ingresar data en search_input: {e}")
                continue
        logging.info("No se pudo localizar un campo de búsqueda válido.")
        return None
    def insert_text(self,text,input_element):
        for char in text:
            input_element.send_keys(char)
            self.random_time(0.05,0.25)
    def obtener_posts(self, driver):
        try:
            time.sleep(1)  # Espera inicial de 1 segundo
            
            feed_div = None
            # Intentar localizar el contenedor principal con múltiples selectores
            for selector in self.selectors_divs:
                try:
                    feed_div = WebDriverWait(driver, 30).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if feed_div:
                        break
                except Exception as e:
                    logging.warning(f"Error al localizar feed_div con el selector {selector}: {e}")
                    continue

            if not feed_div:
                logging.error("No se pudo localizar el contenedor principal 'feed_div'.")
                return []

            # Intentar localizar los elementos dentro de feed_div
            for selector in self.selectors_divs_one:
                try:
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    divs = feed_div.find_elements(By.CSS_SELECTOR, selector)
                    if divs:
                        return divs
                except Exception as e:
                    logging.warning(f"Error al localizar divs unitarios con el selector {selector}: {e}")
                    continue

            # Si no se encuentran elementos
            logging.error("No se encontraron elementos unitarios dentro de 'feed_div'.")
            return []

        except TimeoutException as e:
            logging.error(f"Error: Timeout esperando elementos: {e}")
        except Exception as e:
            logging.error(f"Error inesperado en obtener_posts: {e}")

        # Retornar una lista vacía en caso de error
        return []
    def scroll_hasta_el_final_post(self,driver,min_scroll,max_scroll,min_s,max_s):
        scroll_distance = random.randint(min_scroll, max_scroll)  # Randomize scroll distance
        #logging.info("La distnacia movida en post fue o es :" , scroll_distance)
        current_scroll_position = driver.execute_script("return window.pageYOffset;")
        target_scroll_position = current_scroll_position + scroll_distance
        driver.execute_script(f"window.scrollTo(0, {target_scroll_position});")
        time.sleep(random.uniform(min_s, max_s))  # Randomize delay to mimic human behavior   
    def login(self):
        max_attempts = len(self.credentials)
        attempt = 0
        failed_credentials = set() 
        try:
                    self.stop_event = threading.Event()
                    self.captcha_thread = threading.Thread(target=self.monitor_captcha, args=(self.driver, self.stop_event))
                    self.captcha_thread.start()
        except Exception as e:
            logging.error(f"Error al crear el hilo de CAPTCHA: {e}")


        while attempt < max_attempts and self.credentials:
            # Elegir credenciales que no estén en el conjunto de fallidas
            email, password = random.choice(self.credentials)
            if (email, password) in failed_credentials:
                continue  # Ignorar credenciales ya fallidas

            try:
                target_url = 'https://www.tiktok.com/login/phone-or-email/email?lang=es'
                self.driver.get(target_url)
                self.random_time(1, 2)

                # Monitorear CAPTCHA en un hilo
                
                # Introducir email
                try:
                    email_input = WebDriverWait(self.driver, 15).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='username']"))
                    )
                    email_input.click()
                    self.insert_text(email, email_input)
                except Exception as e:
                    logging.error(f"Error al ingresar el email: {e}")
                    failed_credentials.add((email, password))
                    continue  # Intentar con otras credenciales

                # Introducir contraseña
                try:
                    password_input = WebDriverWait(self.driver, 35).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
                    )
                    self.insert_text(password, password_input)
                except Exception as e:
                    logging.error(f"Error al ingresar la contraseña: {e}")
                    failed_credentials.add((email, password))
                    continue

                # Hacer clic en el botón de inicio de sesión
                try:
                    login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                    login_button.click()
                    self.random_time(1, 1.5)
                    logging.info("Por favor, resuelve el CAPTCHA manualmente.")
                except Exception as e:
                    logging.error(f"Error al hacer clic en el botón de inicio de sesión: {e}")
                    failed_credentials.add((email, password))
                    continue

                # Verificar errores de inicio de sesión
                try:
                    error_message = WebDriverWait(self.driver, 8).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "div[type='error'] > span"))
                    ).text
                    if "Cuenta o contraseña incorrecta" in error_message or "Este usuario no existe" in error_message:
                        logging.info(f"Credenciales incorrectas con {email} & {password}")
                        email_input.clear()
                        password_input.clear()
                        failed_credentials.add((email, password))
                        continue  # Probar con otras credenciales
                    elif "Se ha alcanzado el número máximo de intentos." in error_message:
                        logging.info("Se alcanzó el máximo de intentos. Reintentando...")
                        for _ in range(3):
                            try:
                                login_button.click()
                                self.random_time(0.3, 1.5)
                            except Exception as e:
                                logging.error(f"Error al reintentar inicio de sesión: {e}")
                        failed_credentials.add((email, password))
                        continue  # Probar con otras credenciales

                except TimeoutException:
                    logging.info("Inicio de sesión exitoso.")
                    return True  # Salir si inicia sesión correctamente

            except Exception as e:
                logging.error(f"Error durante el inicio de sesión: {e}")
                failed_credentials.add((email, password))
                continue

            finally:
                attempt += 1
                if hasattr(self, 'captcha_thread') and self.captcha_thread.is_alive():
                    logging.info("Esperando que el hilo de CAPTCHA login termine...")
                    self.terminar_hilo()
                else:    
                    logging.info("Hilo de CaPTCHA login murio que raro")
                logging.info("Hilo de CAPTCHA login ha finalizado correctamente.")    
        logging.info("No se pudo iniciar sesión con ninguna credencial.")
        return False
    def obtener_fecha(self,fecha_str):
        # Obtener la fecha actual
        fecha_actual = datetime.now()
        
        # Si la fecha está en formato relativo, como "hace 5h"
        if "hace" in fecha_str and "h" in fecha_str:
            try:
                horas_ago = int(fecha_str.split("hace")[1].strip().replace("h", "").strip())
                fecha_comentario = fecha_actual
                logging.info(f"Fecha de comentario (hace {horas_ago} horas): {fecha_comentario}")
                return fecha_comentario
            except Exception as e:
                logging.error(f"Error al procesar la fecha relativa: {e}")
                return fecha_actual  # Si hay error, devolver la fecha actual
        
        # Si la fecha está en formato mes/día, como "07-28" o "12-15"
        elif len(fecha_str.split("-")) == 2:
            try:
                mes, dia = map(int, fecha_str.split("-"))
                # Añadir el año actual
                fecha_comentario = fecha_actual.replace(month=mes, day=dia, year=fecha_actual.year)
                logging.info(f"Fecha de comentario (solo mes y día): {fecha_comentario}")
                return fecha_comentario
            except ValueError as e:
                logging.error(f"Error al procesar la fecha mes/día: {e}")
                return fecha_actual 
        elif len(fecha_str.split("-")) == 3:
            try:
                año, mes, dia = map(int, fecha_str.split("-"))
                fecha_comentario = datetime(año, mes, dia)
                logging.info(f"Fecha de comentario (fecha completa): {fecha_comentario}")
                return fecha_comentario
            except ValueError as e:
                logging.error(f"Error al procesar la fecha completa: {e}")
                return fecha_actual  # Si hay error, devolver la fecha actual
        
        # Si no es ninguno de los formatos anteriores, devolver la fecha actual
        else:
            logging.info(f"Fecha no reconocida, devolviendo fecha actual: {fecha_actual}")
            return fecha_actual     # Si hay error, devolver la fecha actual    
    def obtener_video(self,enlace,publicacion_id):
         try:
                with self.conexion.connection.cursor() as cursor:
                    consulta_verificacion = "SELECT id FROM video WHERE url = %s AND publicacion_id =%s"
                    cursor.execute(consulta_verificacion, (enlace,publicacion_id))
                    resultado = cursor.fetchone()
                    
                    if resultado is None and enlace is not None:
                            consulta = "INSERT INTO video (url, publicacion_id) VALUES (%s, %s) "
                            cursor.execute(consulta, (enlace,publicacion_id))
                            self.conexion.connection.commit() 
                            logging.info("Comentario video insertado con éxitos")
                    else:
                        logging.info(f"El id repetido en videos es: {resultado}")
                        logging.info("NO SE INSERTO VIDEO ELEMENTO REPETIDO")        
         except psycopg2.Error as e:
                        logging.error(f"Error en la base de datos con la tabla videos: {e}")
         except Exception as e:
                        logging.error(f"Algo está pasando conn el video insertado: {e}")    
    def obtener_comentarios(self,driver,publicacion_id):
        try:
                event=True
                comentarios_vistos = set()
                time.sleep(1)
                # Obtén la nueva URL actual
                contador_repeticiones = 0 
                contador_comentarios_repetidos = 0
                longitud_anterior = -1 
                while event: 
                # Llama al siguiente método
                    try:
                        coments= self.obtener_comentario(driver)
                        div_scrolling = driver.find_element(By.CSS_SELECTOR, 'div.css-1qp5gj2-DivCommentListContainer.ekjxngi3')
                        # Desplaza el ul hacia abajo (simulando el scroll al final)
                        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", div_scrolling)
                        # Simula que el cursor está sobre el ul (esto activa interacciones como el scroll)
                        actions = ActionChains(driver)
                        actions.move_to_element(div_scrolling).perform()
                    except Exception as e:
                        logging.info(f"No contiene comentarios")
                        pass
                    longitud_actual = len(coments)
                    if longitud_actual == longitud_anterior:
                        contador_repeticiones += 1  # Incrementa el contador si es igual
                    else:
                        contador_repeticiones = 0  # Reinicia el contador si no es igual
                    # Actualiza la longitud anterior con la longitud actual
                    longitud_anterior = longitud_actual
                    # Si la longitud se ha repetido 20 veces, cambia event a False
                    if contador_repeticiones >= 3:
                        logging.info("La longitud de comentarios se ha repetido 3 veces. Terminando la extracción de comentarios del post actual.")
                        event = False  # Termina el bucle
                        pass
                    try:
                            i=0
                            logging.info(f"cantidad de comentarios {len(coments)}")
                            for coment in coments:
                                contenido_coment=coment.text
                                if contenido_coment not in comentarios_vistos:  # Verifica si el texto ya fue procesado
                                    comentarios_vistos.add(contenido_coment)
                                    logging.info(f"Estamos en el iterador {i}")
                                    
                                    try :
                                        user_coment = WebDriverWait(coment, 35).until(
                                        EC.visibility_of_element_located((By.CSS_SELECTOR, "span[data-e2e='comment-username-1']")))
                                    # Obtener el nombre del usuario
                                        usuario = user_coment.text
                                        # Espera hasta que el enlace al avatar del usuario esté visible
                                        user_ref = WebDriverWait(coment, 15).until(
                                            EC.visibility_of_element_located((By.CSS_SELECTOR, "a[data-e2e='comment-avatar-1']"))).get_attribute('href')
                                        logging.info(f"usuario comentador:  {usuario}")
                                        logging.info(f"user_enlace: {user_ref}")
                                    except Exception as e:
                                        logging.error(f"Problemas al obtener uno des los elementos usuario enlace , o usuario comentador {e}")
                                    
                                    try:
                                        descripcion_comentario= coment.find_element(By.CSS_SELECTOR, "p[data-e2e='comment-level-1'] span").text
                                        logging.info(f"comentario {descripcion_comentario}")
                                    except:
                                        logging.info("no tiene un comentario")
                                    try:
                                        fecha = WebDriverWait(coment, 10).until(
                                                EC.visibility_of_element_located((By.CSS_SELECTOR, "span[data-e2e='comment-time-1']"))
                                            )
                                        fecha=fecha.text
                                        fecha_comentario=self.obtener_fecha(fecha)
                                        #logging.info(f"Fecha por si sola : {fecha}")
                                        logging.info(f"Fecha de comentario : {fecha_comentario}")
                                    except Exception as e:
                                        logging.error(f"Error dentro de obenter fecha {e}")
                                        pass     
                                    try:  
                                        with self.conexion.connection.cursor() as cursor:
                                            consulta_verificacion = "SELECT id FROM comentario WHERE usuario = %s AND descripcion_comentario = %s AND  publicacion_id= %s"
                                            cursor.execute(consulta_verificacion, (usuario, descripcion_comentario,publicacion_id ))
                                            resultado = cursor.fetchone()
                                            if(resultado == None):
                                                consulta = "INSERT INTO comentario (publicacion_id,enlace_usuario,fecha, usuario,descripcion_comentario) VALUES (%s,%s,%s,%s,%s) RETURNING id"
                                                cursor.execute(consulta, (publicacion_id,user_ref,fecha_comentario,usuario, descripcion_comentario))
                                                self.conexion.connection.commit()
                                                comentario_id = cursor.fetchone()[0]
                                                logging.info(f"Comentario insertada con éxito.")
                                            else:
                                                logging.info("comentario ya doble y repetido,no ingestado a la db")
                                                contador_comentarios_repetidos += 1   
                                                if(contador_comentarios_repetidos >= 4):
                                                    logging.info("Se reptitio mas de 4 comentarios , obviamos los demas comentarios")
                                                    event=False 
                                                    break
                                                                    
                                    except psycopg2.Error as e:
                                                logging.error(f"Error en la base de datos con la comentario  {e}" )
                                    except Exception as e:
                                                logging.error(f"algo esta mal con la insercion del comentario {e}")
                                i +=1;
                                
                    except Exception as e:
                        logging.error(f"Error en el desarrollo del bucle {e}")
                        pass            
        except Exception as e:
            logging.error("Ocurrio un error obtiendo lo comentarios probablemente dentro del bucle")
            pass    
    def post_relacionado(self,driver,topic,j):
        try:
            post_contenido= WebDriverWait(driver, 15).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "div > div.css-1u3jkat-DivDescriptionContentWrapper.e1mecfx011")))
            post_contenido = post_contenido.text   
            logging.info(f"post contenido total:  {post_contenido}")
            topic = topic.replace('#', '')
            if topic not in post_contenido:
                    j += 1;
                    logging.info(f"Contador {j} publicaciones sin el contenido del topic {topic} ")
            return j 
        except Exception as e:
            logging.error(f"Error en obterner la relacionde posts {e}")
    def terminar_hilo(self):
        try:
            if self.stop_event and self.captcha_thread:
                if self.captcha_thread.is_alive():
                    logging.info("Deteniendo el hilo de CAPTCHA...")
                    self.stop_event.set()  # Señaliza al hilo que debe detenerse
                    self.captcha_thread.join()  # Espera a que el hilo termine
                    logging.info("Hilo de CAPTCHA detenido correctamente.")
        except Exception as e:
            logging.error(f"Error al cerrar el hilo: {e}")        
    def extraer_data(self,driver,topic):
        try:    
            self.stop_event = threading.Event()
            self.captcha_thread = threading.Thread(target=self.monitor_captcha, args=(self.driver, self.stop_event))
            self.captcha_thread.start()
            logging.info("Hilo de CAPTCHA iniciado exitosamente en extraer data.")
        except Exception as e:
            logging.error(f"Error as {e} in thread creation")

        try:
            elementos_vistos = set()
            event =True  
            j=0
            contador_repeticiones = 0  # Contador para verificar repeticiones
            longitud_anterior = -1  # Inicializamos en -1 para que sea diferente de la primera longitud
            logging.info("Ingrese a la funcion extraer data")
            try:
                while event:  # Bucle infinito hasta que se detenga manualmente
                    try:
                        self.scroll_hasta_el_final_post(driver,300,400,0,1.5)
                        divs = self.obtener_posts(driver)  # Obtiene los elementos actuales
                        i =0
                       
                        logging.info("Estoy dentro del bucle")
                        #time.sleep(10)
                        longitud_actual = len(divs)
                        logging.info(f'Cantidad total de divs: {longitud_actual}')
                        if longitud_actual == longitud_anterior:
                            contador_repeticiones += 1  # Incrementa el contador si es igual
                        else:
                            contador_repeticiones = 0  # Reinicia el contador si no es igual
                        # Actualiza la longitud anterior con la longitud actual
                        longitud_anterior = longitud_actual
                        # Si la longitud se ha repetido 20 veces, cambia event a False
                        if contador_repeticiones >= 5:
                            logging.info("La longitud de divs se ha repetido 5 veces. Terminando la extracción.")
                            event = False  # Termina el bucle
                        try:
                            for div in divs:
                               
                                post = WebDriverWait(div, 15).until(
                                        EC.visibility_of_element_located((By.CSS_SELECTOR, "div[aria-label='Ver en pantalla completa'] a"))
                                    )
                                post_enlace= post.get_attribute('href')
                                post_contenido=div.text
                                logging.info(f"El enlace del post:  {post_enlace}")
                                if post_enlace not in elementos_vistos:  # Verifica si el texto ya fue procesado
                                    elementos_vistos.add(post_enlace)
                                    post.click()
                                    
                                    j = self.post_relacionado(driver, topic,j)
                                    
                                    if j > 2:
                                        
                                        logging.info("Se encontraton 2 publicaciones sin el tema a buscar")                                    
                                        try:
                                            close_modal = WebDriverWait(driver, 20).until(
                                                EC.visibility_of_element_located((By.CSS_SELECTOR, "button[aria-label='Cerrar']"))
                                            )
                                            close_modal.click()
                                            logging.info("Modal cerrado correctamente.")
                                        except Exception as e:
                                            logging.error(f"Error al cerrar el modal: {e}")
                                        finally:
                                            event = False  # Detener el bucle while
                                            break 
                                        

                                         
                                    try:
                                        post_descripcion= WebDriverWait(driver, 15).until(
                                                EC.visibility_of_element_located((By.CSS_SELECTOR, "h1[data-e2e='browse-video-desc']")))
                                        post_descripcion = post_descripcion.text   
                                        logging.info(f"descripcion post:  {post_descripcion}")   
                                        
                                        
                                        usuario =WebDriverWait(driver, 15).until(
                                                EC.visibility_of_element_located((By.CSS_SELECTOR, "span[data-e2e='browse-username'] > span"))
                                            )
                                        usuario=usuario.text  
                                        logging.info(f"El usuario:  {usuario}")
                                        usuario_enlace= WebDriverWait(driver, 15).until(
                                                EC.visibility_of_element_located((By.CSS_SELECTOR, "a[data-e2e='browse-user-avatar']"))
                                            )
                                        usuario_enlace=usuario_enlace.get_attribute('href')    
                                        logging.info(f"El enlace de usuario:  {usuario_enlace}")

                                        
                                    except  Exception as e:
                                        logging.error(f"El error es {e}")  
                                    self.random_time(0.3,1)    
                                    try:
                                        post_likes= WebDriverWait(driver, 15).until(
                                                EC.visibility_of_element_located((By.CSS_SELECTOR, "strong[data-e2e='browse-like-count']")))
                                        post_likes = post_likes.text   
                                        logging.info(f"El numero de likes del post es:  {post_likes}")                                 
                                        fecha= WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.CSS_SELECTOR,"span[data-e2e='browser-nickname']> span:nth-of-type(3)"))).text
                                        fecha_post=self.obtener_fecha(fecha)
                                        
                                        logging.info(f"la fecha de la publicacion es:  {fecha_post}")    
                                    except  Exception as e:
                                        logging.error(f"El error es {e}")  
                                    self.random_time(0.3,1) 
                                    #logging.info("Antes de ingestar data a la db")
                                    try:
                                        with self.conexion.connection.cursor() as cursor:
                                            consulta_verificacion = """SELECT id FROM publicacion
                                                                        WHERE descripcion = %s AND usuario = %s AND enlace = %s """
                                            cursor.execute(consulta_verificacion, (post_descripcion, usuario,post_enlace))
                                            resultado = cursor.fetchone()
                                            # Si no existe, insertar
                                            #logging.info(f"Aun todo bien resultado : {resultado}")
                                            if resultado is None:
                                                consulta_insercion = """INSERT INTO publicacion (descripcion,fecha, usuario,likes,enlace,usuario_enlace)
                                                                        VALUES (%s,%s,%s,%s,%s,%s)
                                                                        RETURNING id"""
                                                cursor.execute(consulta_insercion, (post_descripcion,fecha_post,usuario,post_likes, post_enlace,usuario_enlace ))
                                                publicacion_id = cursor.fetchone()[0]
                                                #logging.info("El id publiacion es resultaod none: ", publicacion_id)
                                                self.conexion.connection.commit()
                                                logging.info(f"Publicación insertada con éxito. ID de la publicación: {publicacion_id}")
                                            else:
                                                publicacion_id = resultado[0]
                                                logging.info(f"El id publiacion es duplicada no se inserto : {publicacion_id}")
                                            logging.info(f"el id de publicaoin es {publicacion_id}")    
                                    except psycopg2.Error as e:
                                                logging.error(f"Error en la base de datos con la publicación  con id : {publicacion_id}  {e} ")
                                    except Exception as e:
                                                logging.error(f"algo esta mal con la insercion de la publicacion con id : {publicacion_id} ")
                                    logging.info(f"Actual valor del contador de iteraciones que se repiten :{j} en la publicacion {publicacion_id}")
                                    try:
                                        self.obtener_video(post_enlace,publicacion_id)
                                    except Exception as e:
                                        logging.info(f"Algun porblema sucede en {e} ")
                                    self.obtener_comentarios(driver,publicacion_id)       
                                    logging.info("Antes de cerrar en modal")
                                    try:
                                        close_modal = WebDriverWait(driver, 20).until(
                                                EC.visibility_of_element_located((By.CSS_SELECTOR, "button[aria-label='Cerrar']"))
                                            )                                    
                                        close_modal.click()    
                                    except Exception as e:
                                        logging.error(f"Error en cerrar el modal {e}")    
                                    yield {
                                "post_enlace": post_enlace,
                                "usuario": usuario,
                                "usuario_enlace": usuario_enlace,
                                "descripcion": post_descripcion,
                                "likes": post_likes,
                                "fecha": fecha
                            }

                        except Exception as e:
                            logging.error(f"El error  antes de iterar data dentro de los divs obtenidos{e}")                            
                    except:
                        pass 
            except:
                pass                 
        except Exception as e:
            logging.error(f"Hubo un error al obtener data {e}")    
        finally:
            if self.captcha_thread.is_alive():
                logging.info("Esperando que el hilo de CAPTCHA extraer data termine...")
                self.stop_event.set()  # Se activa el stop_event para que el hilo de CAPTCHA termine
                self.captcha_thread.join()  # Espera a que el hilo termine
            else:    
                logging.info("hilo de CaPTCHA extraer data murio que raro")
            logging.info("Hilo de CAPTCHA extraer data ha finalizado correctamente.")
        pass    
    def procesar_extraccion(self):
        #logging.info(f"Acceso exitoso con las credenciales : {email}")
        self.configurar_logger()
        logging.info("Iniciando scrapeo de perfiles ...")
        self.config.read('topics.conf')
        try:
            if not self.login():
                logging.info("Ingreso exitoso")

        except Exception as e:
            logging.error(f"Error en login: {e}")

        try:
            if 'DEFAULT' in self.config and 'topic' in self.config['DEFAULT']:
                topics_str = self.config.get('DEFAULT', 'topic')
                self.topics = [topic.strip() for topic in topics_str.strip("[]").replace("'", "").split(",")]
            else:
                logging.info("La opción 'topic' no se encontró en la sección 'DEFAULT'")
            logging.info(f"Temas a buscar: {self.topics}")
        except Exception as e :
                logging.info(f"Problemas con  topics  {e}" )
        tipo = "TEMA A BUSCAR"
        for topic in self.topics:
            for selector in self.selectors_boton_busqueda:
                try:
                    search_icon = WebDriverWait(self.driver, 25).until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    ActionChains(self.driver).move_to_element(search_icon).click().perform()
                except Exception as e:
                    logging.error(f"Error al ubicar busqueda to click {e}")
                    continue 
            try:    
                for selector in self.selectors_busqueda:
                    try:
                        search_input = WebDriverWait(self.driver, 20).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        if search_input:
                            break  # Devuelve si se encuentra el elemento
                    except Exception as e:
                        logging.error(f"Error al tratar de obtener o ingresar data en search_input: {e}")
                        continue
                logging.info("No se pudo localizar un campo de búsqueda válido.")
                if search_input is None:
                    logging.info("No se pudo localizar un campo de búsqueda válido.")
                    continue
                search_input.click()  # Asegurarse de que esté enfocado
                search_input.send_keys(Keys.CONTROL + "a")  # Seleccionar todo el texto
                search_input.send_keys(Keys.DELETE)
                search_input.send_keys(topic)
                search_input.send_keys(Keys.RETURN)
                try:
                    with self.conexion.connection.cursor() as cursor:
                            consulta_insercion = """INSERT INTO busqueda (busqueda,typo)
                                                    VALUES (%s,%s)"""
                            cursor.execute(consulta_insercion, (topic,tipo))
                            #logging.info("El id publiacion es resultaod none: ", publicacion_id)
                            self.conexion.connection.commit()
                            logging.info(f"Busqueda insertada con éxito.")  
                except psycopg2.Error as e:
                            logging.error(f"Error en la base de datos con la Busqueda {e}")
                except Exception as e:
                            logging.error(f"algo esta mal con la insercion de la Busqueda ")
            except Exception as e:
                logging.error(f"El error de iteracino de busqueda es {e}")
                continue    
            try:
                for dato in self.extraer_data(self.driver,topic):
                    logging.info('siguiente post:')
            except Exception as e:
                logging.error(f"Error antes de entrar a etraer datao por dato del for {e}")        
            logging.info(f"Terminando de extraer tema: {topic}")
        # Salir del bucle al encontrar credenciales válidas
    def cerrar_conexion(self):
        try:
            logging.info(f"Estado del cierre. {self.driver}")
            # Cerrar el navegador
            if self.driver:
                self.driver.quit()
                logging.info("Conexión cerrada y navegador cerrado correctamente.")
        except Exception as e:
            logging.error(f"Error al cerrar la conexión o el navegador: {e}")

# Inicializar Selenium y ejecutar el inicio de sesión
def main():
    
    try:
        scraper_tk = Scrape_topic_tk() 
        scraper_tk.procesar_extraccion()
        scraper_tk.cerrar_conexion()   
    except KeyboardInterrupt:
        logging.info("Programa cancelado por el usuario.")
        scraper_tk.cerrar_conexion()
    except Exception as e:
        logging.error(f"Error inesperado: {e}")
        scraper_tk.cerrar_conexion()
    except Exception as e :
     logging.error(f"Erro en ejecutar el codigo con erroe en {e}")


if __name__ == "__main__":
    
    main()
