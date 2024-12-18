# TIKTOK_SCRAPER

## Setup Instructions

### Database Setup
1. **Create the database**: Execute the `tiktok_db.sql` file in your PostgreSQL environment to set up the required tables.
2. **Update connection parameters**: Edit the connection settings (`user`, `password`, `port`, `localhost`) in the code to match your PostgreSQL setup.

### Required Files
Ensure the following configuration files are properly configured:
- **`topics.conf`**: Specify topics for scraping.
- **`perfil.conf`**: List of target profiles.
- **`apikeys.conf`**: Contains the API key for solving captchas.
- **`db_credentials.ini`**: Stores database connection details.

You cand find the apikey from :https://www.sadcaptcha.com/

```conf
[CAPTCHA_SOLVER]
api_key= 'YOUR_APIKEY'
```
```conf
[DEFAULT]
perfiles=['https://www.tiktok.com/@valeria.zevallos0','https://www.tiktok.com/@manuellopez5193']
```
### Credentials Configuration
Add your login credentials to the `credentials.conf` file in this format:
```conf
emailkey1=example1@gmail.com
usernamekey1=ExampleUser1
passwordkey1=ExamplePassword1

emailkey2=example2@gmail.com
usernamekey2=ExampleUser2
passwordkey2=ExamplePassword2
```
### Dependencies
Ensure the following software and libraries are installed:

- **`Python 3+`**
- **`PostgreSQL`**
- **`Selenium`**
Install required Python libraries with pip:
```bash
pip install selenium fake-useragent psycopg2 pyautogui logging undetected-chromedriver selenium-stealth selenium-wire tiktok-captcha-solver
```
### Running the Script

To execute the scraping code, run the following command:

```bash

python scrape_main_ig.py --funcion_ejecutar perfil_login #ejecuta scrape de perfile con varios perfiles
python scrape_main_ig.py --funcion_ejecutar busqueda_login #jecuta scrape de busqueda con varios perfiles
python scrape_main_ig.py --funcion_ejecutar perfil #jecuta scrape perfile con sesion de tu navegador
python scrape_main_ig.py --funcion_ejecutar busqueda # ejecuta scrape busqueda con sesion de tu navegador

```
## Appendix
### Limit extracion for search

In this code snippet, you're applying a limitation on the extraction process to avoid gathering irrelevant or unwanted data. The goal is to stop processing further data if certain conditions are met, specifically if more than two entries do not match the search criteria. Here's an improved explanation of how it works:
```python
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
```
### Adding route

The following line defines the path to the Chrome user data directory for use you own session of tiktok in your browser:

```python
profile_path = r"C:\Users\Usuario\AppData\Local\Google\Chrome\User Data"
```
### Adding Profiles

To add profile credentials, save them in the `credentials.conf` file using the following format:

```conf
[DEFAULT]
emailkey1=blrdmanrique@gmail.com
usernamekey1=AbelardoMa65534
passwordkey1=Abelardo_X_23_01_00

emailkey2=something1
usernamekey2=something2
passwordkey2=something3

emailkey3=some_example@gmail.com
usernamekey3= usernamekey_example
passwordkey3=password_example

emailkey4=some_example1@gmail.com
usernamekey4= usernamekey1_example
passwordkey4=password2_example
```
### Operating Videos
The `process_video1.py` script transforms the links from the PostgreSQL database into MP4 files, which can be used for future deep learning applications or any other purpose. These files are saved in their respective folders, with each file named based on its ID and the corresponding publication ID, allowing easy identification in the database. The video processing logic is executed with each command previously explained, whether for logged-in users or non-logged-in users, for search purposes, or profile scraping.

 
### Run separately
If you only want to get videos and dont want scrape more , use this comand

```bash

py process_video1.py
````