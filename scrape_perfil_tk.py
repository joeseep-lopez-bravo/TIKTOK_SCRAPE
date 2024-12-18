from selenium import webdriver
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException,WebDriverException,TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from seleniumwire import webdriver
from datetime import datetime, timedelta
from selenium_stealth import stealth
from tiktok_captcha_solver import SeleniumSolver
import configparser
import random
import threading
import time
from selenium.webdriver.common.by import By
import psycopg2
import logging
import signal
import sys
from db_connection_tk import DatabaseConnection

class Scraper_tiktok_perfiles():
    def __init__(self):        
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--start-maximized')
        profile_path = r"C:\Users\Usuario\AppData\Local\Google\Chrome\User Data"
        chrome_options.add_argument(f"user-data-dir={profile_path}")
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.stop_event = None
        self.captcha_thread = None
    
        self.driver = uc.Chrome(
            headless=False, 
            options=chrome_options  # Opciones de Chrome
        )
        
        # Cargar configuración de credenciales
        stealth(self.driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
        )
        
        self.config = configparser.ConfigParser()
        self.config.read('api_keys.conf')
        self.api_key_captcha = self.config.get('CAPTCHA_SOLVER', 'api_key', fallback=None)
        self.sadcaptcha = SeleniumSolver(
            self.driver,
            self.api_key_captcha,
            mouse_step_size=1,  # Ajustar velocidad del mouse
            mouse_step_delay_ms=10  # Ajustar delay del mouse
        )
        # Selectores de scraping
        self.selectors = [
            "div.x1qjc9v5.x972fbf.xcfux6l.x1qhh985.xm0m39n.x9f619.x1lliihq.xdt5ytf.x2lah0s.x1a7h2tk.x14miiyz.xat24cr.x1mh8g0r.xexx8yu.x4uap5.x18d9i69.xkhd6sd.x1n2onr6.x11njtxf.xph46j.x9i3mqj.xcghwft.x1bzgcud.xgczaz5.x1rzo0p5.x1guec7k",
            "div.x1qjc9v5.x972fbf.xcfux6l.x1qhh985.xm0m39n.x9f619.x1lliihq.xdt5ytf.x2lah0s.xrbpyxo.x1a7h2tk.x14miiyz.xat24cr.x1mh8g0r.xexx8yu.x4uap5.x18d9i69.xkhd6sd.x1n2onr6.x11njtxf.x1bfs520.xph46j.x9i3mqj.xcghwft.x1bzgcud.xhdunbi"
        ]
        
        # Inicializar la conexión a la base de datos
        self.conexion = DatabaseConnection()
        self.conexion.crear_conexion()
    def random_time(self, min_time ,max_time):
        delay = random.uniform(min_time, max_time)
        time.sleep(delay)
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
                time.sleep(1)  # Evita uso excesivo de recursos     
    def detectar_captcha(self, driver):
        try:
            captcha = driver.find_element(By.CSS_SELECTOR, 'div.TUXModal.captcha-verify-container')  # Reemplaza con el selector correcto
            return True
        except Exception:
            return False            
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
                logging.info(f"Error al tratar de obtener o ingresar data en search_input: {e}")
                continue
        logging.info("No se pudo localizar un campo de búsqueda válido.")
        return None
    def configurar_logger(self):
        # Configuración básica del logger
        logging.basicConfig(filename='Logs_Scraper_Perfil_TikTok.log',  # Archivo donde se guardarán los logs
                            level=logging.INFO,     # Nivel de registro, en este caso errores
                            format='%(asctime)s - %(levelname)s - %(message)s',  # Formato del log
                            datefmt='%Y-%m-%d %H:%M:%S')  # Formato de la fecha y hora       
    def obtener_fecha(self, fecha_str):
    # Obtener la fecha actual
        fecha_actual = datetime.now()

        # Si la fecha está en formato relativo, como "hace 5h" o "hace 5d"
        if "hace" in fecha_str:
            try:
                if "h" in fecha_str:
                    horas_ago = int(fecha_str.split("hace")[1].strip().replace("h", "").strip())
                    fecha_comentario = fecha_actual - timedelta(hours=horas_ago)
                    logging.info(f"Fecha de comentario (hace {horas_ago} horas): {fecha_comentario}")
                    return fecha_comentario
                elif "d" in fecha_str:
                    dias_ago = int(fecha_str.split("hace")[1].strip().replace("d", "").strip())
                    fecha_comentario = fecha_actual - timedelta(days=dias_ago)
                    logging.info(f"Fecha de comentario (hace {dias_ago} días): {fecha_comentario}")
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

        # Si la fecha está en formato completo año/mes/día, como "2023-07-28"
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
            return fecha_actual
    def obtener_posts(self,driver):
        try:
            time.sleep(1)  # Espera inicial de 1 segundo
            # Intentar localizar el contenedor principal con múltiples selectores
            try:
                feed_div = WebDriverWait(driver, 23).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "div[data-e2e='user-post-item-list']"))
                )   
            except Exception as e:
                logging.info(f"Error al localizar feed_div  {e}")
                pass

            if not feed_div:
                logging.info("No se pudo localizar el contenedor principal 'feed_div'.")
                return []
            # Intentar localizar los elementos dentro de feed_div          
            try:
                WebDriverWait(driver, 23).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.css-1uqux2o-DivItemContainerV2.e19c29qe17"))
                )
                divs = feed_div.find_elements(By.CSS_SELECTOR, "div.css-1uqux2o-DivItemContainerV2.e19c29qe17")
                return divs
            except Exception as e:
                logging.info(f"Error al localizar divs unitarios con el selector  {e}")
                  
            # Si no se encuentran elementos
            logging.info("No se encontraron elementos unitarios dentro de 'feed_div'.")
            return []

        except TimeoutException as e:
            logging.info(f"Error: Timeout esperando elementos: {e}")
        except Exception as e:
            logging.info(f"Error inesperado en obtener_posts: {e}")

        # Retornar una lista vacía en caso de error
        return []
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
                                    logging.info("Estamos en el iterador" , i)
                                    
                                    try :
                                        user_coment = WebDriverWait(coment, 35).until(
                                        EC.visibility_of_element_located((By.CSS_SELECTOR, "span[data-e2e='comment-username-1']")))
                                    # Obtener el nombre del usuario
                                        usuario = user_coment.text
                                        # Espera hasta que el enlace al avatar del usuario esté visible
                                        user_ref = WebDriverWait(coment, 35).until(
                                            EC.visibility_of_element_located((By.CSS_SELECTOR, "a[data-e2e='comment-avatar-1']"))).get_attribute('href')
                                        logging.info(f"usuario comentador:  {usuario}")
                                        logging.info(f"user_enlace: {user_ref}")
                                    except Exception as e:
                                        logging.info(f"Problemas al obtener uno des los elementos usuario enlace , o usuario comentador {e}")
                                    
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
                                        logging.info(f"Error dentro de obenter fecha {e}")
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
                        logging.info(f"Error en el desarrollo del bucle {e}")
                        pass            
        except Exception as e:
            logging.error("Ocurrio un error obtiendo lo comentarios probablemente dentro del bucle")
            pass    
    def perfil_generador(self,perfil_links):
        for perfil_link in perfil_links:
            yield perfil_link
    def scrolling_down(self,driver,min_scroll,max_scroll,min_s,max_s):
        scroll_distance = random.randint(min_scroll, max_scroll)  # Randomize scroll distance
        #logging.info("La distnacia movida en post fue o es :" , scroll_distance)
        current_scroll_position = driver.execute_script("return window.pageYOffset;")
        target_scroll_position = current_scroll_position + scroll_distance
        driver.execute_script(f"window.scrollTo(0, {target_scroll_position});")
        time.sleep(random.uniform(min_s, max_s))  
    def extraer_data(self,driver):
        try:
            self.stop_event = threading.Event()
            self.captcha_thread = threading.Thread(target=self.monitor_captcha, args=(self.driver, self.stop_event))
            self.captcha_thread.start()
            logging.info("Hilo de CAPTCHA iniciado exitosamente.")
        except Exception as e:
            logging.error(f"Error al crear el hilo de CAPTCHA: {e}")
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
                            nickname = WebDriverWait(driver, 15).until(
                                        EC.visibility_of_element_located((By.CSS_SELECTOR, "h1[data-e2e='user-title']"))
                                    )
                            nickname= nickname.text
                            logging.info(f"El nickname del perfil es : {nickname}")
                            username = WebDriverWait(driver, 15).until(
                                        EC.visibility_of_element_located((By.CSS_SELECTOR, "h2[data-e2e='user-subtitle']"))
                                    )
                            username= username.text
                            logging.info(f"El username del perfil es : {username}")
                            
                            likes_perfil = WebDriverWait(driver, 15).until(
                                        EC.visibility_of_element_located((By.CSS_SELECTOR, "strong[data-e2e='likes-count']"))
                                    )
                            likes_perfil= likes_perfil.text
                            logging.info(f"Los likes del perfil es : {likes_perfil}")
                            
                            perfil_url = driver.current_url
                            logging.info(f"El enlace del perfil que se scrapea: {perfil_url}")
                        except Exception as e:
                            logging.info(f"Error en obtener informcaion del perfil {e}")   
                        try:
                            with self.conexion.connection.cursor() as cursor:
                                consulta_verificacion = """SELECT id FROM perfil
                                                            WHERE username = %s AND nickname = %s AND enlace = %s """
                                cursor.execute(consulta_verificacion, (username, nickname,perfil_url))
                                resultado = cursor.fetchone()
                                # Si no existe, insertar
                                #logging.info(f"Aun todo bien resultado : {resultado}")
                                if resultado is None:
                                    consulta_insercion = """INSERT INTO perfil ( likes,enlace,username,nickname)
                                                            VALUES (%s,%s,%s,%s)
                                                            RETURNING id"""
                                    cursor.execute(consulta_insercion, (likes_perfil,perfil_url,username,nickname ))
                                    perfil_id = cursor.fetchone()[0]
                                    #logging.info("El id publiacion es resultaod none: ", publicacion_id)
                                    self.conexion.connection.commit()
                                    logging.info(f"Perfil insertado con éxito. ID de la publicación: {perfil_id}")
                                else:
                                    perfil_id = resultado[0]
                                    logging.info(f"El id del perfil es duplicada no se inserto : {perfil_id}")
                                logging.info(f"el id de publicaoin es {perfil_id}")    
                        except psycopg2.Error as e:
                                    logging.error(f"Error en la base de datos con la publicación  con id : {perfil_id}  {e} ")
                        except Exception as e:
                                    logging.error(f"algo esta mal con la insercion de la publicacion con id : {perfil_id} ")      
                        time.sleep(1.3)
                        try:
                            for div in divs:

                                post = WebDriverWait(div, 15).until(
                                        EC.visibility_of_element_located((By.CSS_SELECTOR, "div[data-e2e='user-post-item'] a"))
                                    )
                                post_enlace= post.get_attribute('href')
                                post_contenido=div.text
                                logging.info(f"El enlace del post:  {post_enlace}")
                                if post_enlace not in elementos_vistos:  # Verifica si el texto ya fue procesado
                                    elementos_vistos.add(post_enlace)
                                    post.click()
                                    try:
                                        post_descripcion= WebDriverWait(driver, 15).until(
                                                EC.visibility_of_element_located((By.CSS_SELECTOR, "h1[data-e2e='browse-video-desc']")))
                                        post_descripcion = post_descripcion.text   
                                        logging.info(f"descripcion post:  {post_descripcion}")   
                                    except  Exception as e:
                                        post_descripcion=''
                                        logging.info(f"Post No contiene descripcion")   
                                        pass                             
                                    try:
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
                                        logging.info(f"El error es {e}") 
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
                                        logging.info(f"El error es {e}")  
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
                                                consulta_insercion = """INSERT INTO publicacion (descripcion,fecha, usuario,likes,enlace,usuario_enlace,perfil_id)
                                                                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                                                                        RETURNING id"""
                                                cursor.execute(consulta_insercion, (post_descripcion,fecha_post,usuario,post_likes, post_enlace,usuario_enlace ,perfil_id))
                                                publicacion_id = cursor.fetchone()[0]
                                                logging.info(f"El id publiacion es resultaod none:  {publicacion_id}")
                                                self.conexion.connection.commit()
                                                logging.info(f"Publicación insertada con éxito. ID de la publicación: {publicacion_id}")
                                            else:
                                                publicacion_id = resultado[0]
                                                logging.info(f"El id publiacion es duplicada no se inserto : {publicacion_id}")
                                            logging.info(f"el id de publicaoin es {publicacion_id}")    
                                    except psycopg2.Error as e:
                                                logging.info(f"Error en la base de datos con la publicación  con id : {publicacion_id}  {e} ")
                                    except Exception as e:
                                                logging.info(f"algo esta mal con la insercion de la publicacion con id : {publicacion_id} ")
                                    logging.info(f"Actual valor del contador de iteraciones que se repiten en la publicacion {publicacion_id}")
                                    try:
                                        self.obtener_video(post_enlace,publicacion_id)
                                    except Exception as e:
                                        logging.info(f"Algun porblema sucede en {e} ")
                                    #logging.info("Antes de entrar a obtener comentarios")
                                    try:
                                        self.obtener_comentarios(driver,publicacion_id)       
                                    except Exception as e :
                                         logging.info(f"No presenta comentarios ")
                                         pass
                                    #logging.info("Todos estaremos felices al ver que  pasamos comentarios")
                                    #logging.info("Antes de cerrar en modal")
                                    try:
                                        close_modal = WebDriverWait(driver, 20).until(
                                                EC.visibility_of_element_located((By.CSS_SELECTOR, "button[data-e2e='browse-close']"))
                                            )                                    
                                        close_modal.click()    
                                    except Exception as e:
                                        logging.info(f"Error en cerrar el modal {e}")    
                                    yield {
                                "post_enlace": post_enlace,
                                "usuario": usuario,
                                "usuario_enlace": usuario_enlace,
                                "descripcion": post_descripcion,
                                "likes": post_likes,
                                "fecha": fecha
                            }

                        except Exception as e:
                            logging.info(f"El error  antes de iterar data dentro de los divs obtenidos{e}")                            
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
    def scroll_hasta_el_final_post(self,driver,min_scroll,max_scroll,min_s,max_s):
        scroll_distance = random.randint(min_scroll, max_scroll)  # Randomize scroll distance
        #logging.info("La distnacia movida en post fue o es :" , scroll_distance)
        current_scroll_position = driver.execute_script("return window.pageYOffset;")
        target_scroll_position = current_scroll_position + scroll_distance
        driver.execute_script(f"window.scrollTo(0, {target_scroll_position});")
        time.sleep(random.uniform(min_s, max_s))  # Randomize delay to mimic human behavior   
    def cerrar_conexion(self):
        try:
            logging.info(f"Estado del cierre. {self.driver}")
            # Cerrar el navegador
            if self.driver:
                self.driver.quit()
                logging.info("Conexión cerrada y navegador cerrado correctamente.")
        except Exception as e:
            logging.error(f"Error al cerrar la conexión o el navegador: {e}")
    def procesar_extraccion(self):
        try:
            self.configurar_logger()
            target_url = 'https://www.tiktok.com/login/phone-or-email/email?lang=es'
            self.driver.get(target_url)
            logging.info("Iniciando scrapeo de perfiles ...")
            self.config.read('perfiles.conf')
            tipo ="PERFIL"
            try:
                if 'DEFAULT' in self.config and 'perfiles' in self.config['DEFAULT']:
                    perfiles_str = self.config.get('DEFAULT', 'perfiles')
                    perfiles = [perfil.strip() for perfil in perfiles_str.strip("[]").replace("'", "").split(",")]
                else:
                    logging.info("La opción 'perfil' no se encontró en la sección 'DEFAULT'")
                logging.info(f"Temas a buscar: {perfiles}")
            except Exception as e :
                    logging.info(f"Problemas con  perfiles  {e}" )  
            generador_perfil = self.perfil_generador(perfiles)
            for perfil_link in generador_perfil:        
                
                logging.info(f"Accediendo al perfil: {perfil_link}")
                try:
                    with self.conexion.connection.cursor() as cursor:
                            consulta_insercion = """INSERT INTO busqueda (busqueda,typo)
                                                    VALUES (%s,%s)"""
                            cursor.execute(consulta_insercion, (perfil_link,tipo))
                            #logging.info("El id publiacion es resultaod none: ", publicacion_id)
                            self.conexion.connection.commit()
                            logging.info(f"Busqueda insertada con éxito.")  
                except psycopg2.Error as e:
                            logging.error(f"Error en la base de datos con la Busqueda {e}")
                except Exception as e:
                            logging.error(f"algo esta mal con la insercion de la Busqueda ")
                self.driver.get(perfil_link)
                for dato in self.extraer_data(self.driver):
                    logging.info('siguiente post:')
                logging.info(f"Scraping del perfil {perfil_link} completado.")    
            self.cerrar_conexion() 
            pass   
        except Exception as e:
            logging.error(f" Excepcion en procesar extraccion {e}")
        pass   
def signal_handler(sig, frame):
    logging.info('Interrupción recibida, cerrando scraper...')
    if scraper_perfil.driver:
        scraper_perfil.cerrar_conexion()
    sys.exit(0)  # Sale del programa

def main():  
        global scraper_perfil
        try:
            scraper_perfil = Scraper_tiktok_perfiles() 
            signal.signal(signal.SIGINT, signal_handler)  # Registra el manejador de señales
            scraper_perfil.procesar_extraccion()
            scraper_perfil.cerrar_conexion()   
        except KeyboardInterrupt:
            logging.info("Programa cancelado por el usuario.")
            scraper_perfil.cerrar_conexion()
        except Exception as e:
            logging.error(f"Error inesperado: {e}")
            scraper_perfil.cerrar_conexion()

if __name__ == "__main__":
    main()
    