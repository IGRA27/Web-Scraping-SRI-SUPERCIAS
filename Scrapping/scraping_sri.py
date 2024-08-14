from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def configure_browser(headless=False):
    options = webdriver.ChromeOptions()
    
    #IMPORTANTE
    # Aquí defines la ruta al perfil de Chrome
    user_data_dir = r'C:\Users\Omaro\AppData\Local\Google\Chrome\User Data'  # Cambia esto a la ruta correcta
    options.add_argument(f"user-data-dir={user_data_dir}")  # Usa tu perfil de Chrome
    
    if headless:
        options.add_argument("--headless")  # Ejecuta el navegador en modo headless (sin interfaz gráfica)
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver
