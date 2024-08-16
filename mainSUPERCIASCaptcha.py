import os
import tempfile
import requests
import pytesseract #Instalar, y agregar al PATH de las variables del sistema.
import cv2
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from scraping_supercias import configure_browsersupercias

# RESOLVER CAPTCHA
def download_captcha(driver, xpath_image):
    """Descargar la imagen CAPTCHA."""
    objElement = driver.find_element(by="xpath", value=xpath_image)
    imagen_url = objElement.get_attribute("src")
    
    response = requests.get(imagen_url, verify=False)
    
    # Crear un directorio temporal
    temp_dir = tempfile.mkdtemp()
    
    # Definir la ruta del archivo en el directorio temporal
    image_path = os.path.join(temp_dir, "captcha.png")
    
    # Guardar la imagen en el directorio temporal
    with open(image_path, 'wb') as file:
        file.write(response.content)
    
    return image_path

def process_captcha(image_path):
    """Procesar la imagen CAPTCHA y devolver el texto extraído."""
    image = cv2.imread(image_path)
    
    # Convertir la imagen a escala de grises
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Aplicar umbral para binarizar la imagen
    _, binary_image = cv2.threshold(gray_image, 128, 255, cv2.THRESH_BINARY)
    
    # Invertir los colores para que el fondo sea blanco y el texto negro
    inverted_image = cv2.bitwise_not(binary_image)
    
    # Extraer el texto
    extracted_text = pytesseract.image_to_string(image=inverted_image)
    
    # Limpiar el texto extraído
    extracted_text = re.sub(r'[^\w\s]', '', extracted_text)
    extracted_text = re.sub(r'\s+', '', extracted_text)
    
    return extracted_text

def resolver_captcha(driver, xpath_image):
    """Resuelve el CAPTCHA usando los scripts de imagen."""
    image_path = download_captcha(driver, xpath_image)
    captcha_text = process_captcha(image_path)
    return captcha_text

#WEB SCRAPING:
# VERIFICAR DISPONIBILIDAD DE LA PÁGINA
def verificar_disponibilidad_pagina(driver, url, timeout=10):
    try:
        driver.get(url)
        # Espera hasta 10 segundos a que algún elemento de la página sea visible
        WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.TAG_NAME, 'body')))
        return True
    except Exception:
        return False

# INGRESAR RUC Y RESOLVER CAPTCHA
def ingresar_ruc(driver, ruc):    
    retries = 2 #IMPORTANTE EN PRODUCCION
    while retries > 0:
        try:
            input_ruc = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='frmBusquedaCompanias:parametroBusqueda_input']")))
            input_ruc.clear()
            input_ruc.click()
            time.sleep(1)
            input_ruc.send_keys(ruc)
            time.sleep(1)

            ingresado = input_ruc.get_attribute('value')
            if ingresado != ruc:
                print(f"Error al ingresar el RUC. Intentando nuevamente...")
                input_ruc.clear()
                time.sleep(2)
                input_ruc.send_keys(ruc)
                ingresado = input_ruc.get_attribute('value')
                if ingresado != ruc:
                    raise Exception("No se pudo ingresar el RUC correctamente después de varios intentos.")
            input_ruc.send_keys(Keys.RETURN)


            # Esperar hasta 4 segundos para verificar si aparece alguno de los mensajes de "RUC no encontrado"
            try:
                mensaje_error = WebDriverWait(driver, 4).until(
                    EC.any_of(
                        EC.visibility_of_element_located((By.XPATH, "//*[@id='frmBusquedaCompanias:msgBusquedaCompanias']/div/ul/li/span")),
                        EC.visibility_of_element_located((By.XPATH, "//*[@id='frmBusquedaCompanias:msgBusquedaCompanias']/div/span/ul/li/span"))
                    )
                )
                if mensaje_error:
                    # Extraer el texto del mensaje y devolverlo como respuesta JSON
                    mensaje_texto = mensaje_error.text
                    with open(f'{ruc}_error.json', 'w', encoding='utf-8') as f:
                        json.dump({"error": "No existe ninguna compañía cuyo R.U.C. coincida con el parámetro ingresado"}, f, ensure_ascii=False, indent=4)
                    print(f"Error: {mensaje_texto}. Guardado en {ruc}_error.json")
                    return False  # Indicar que el RUC no fue encontrado
            except Exception:
                pass  # Si no aparece el mensaje de error, continuar con el proceso

            # Resolver el CAPTCHA automáticamente
            time.sleep(5)
            captcha_resuelto = resolver_captcha(driver, "//img[@id='frmBusquedaCompanias:captchaImage']")
            input_captcha = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='frmBusquedaCompanias:captcha']")))
            input_captcha.send_keys(captcha_resuelto)
            input_captcha.send_keys(Keys.RETURN)
            break
        except Exception as e:
            retries -= 1
            print(f"Error en ingresar_ruc: {e}. Reintentando...")
            if retries == 0:
                raise e
    return True        

def manejar_captcha(driver, xpath_captcha, xpath_boton_verificar):
    """Intentar resolver el CAPTCHA, si aparece."""
    try:
        time.sleep(3) #agregar 3s antes de capturar
        captcha_resuelto = resolver_captcha(driver, "//*[@id='frmCaptcha:captchaImage']")
        input_captcha = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, xpath_captcha)))
        input_captcha.send_keys(captcha_resuelto)
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath_boton_verificar))).click()
        return True
    except Exception as e:
        print(f"No se encontró CAPTCHA: {e}. Continuando con la extracción de datos...")
        return False

def navegar_y_consultar_ruc(driver, ruc):
    url = 'https://appscvsgen.supercias.gob.ec/consultaCompanias/societario/busquedaCompanias.jsf'
    # si no funciona ese link probar:https://appscvssoc.supercias.gob.ec/consultaCompanias/societario/informacionCompanias.jsf 

    if not verificar_disponibilidad_pagina(driver, url):
        # Si la página no está disponible, devuelve un JSON indicando el estado
        with open(f'{ruc}_error.json', 'w', encoding='utf-8') as f:
            json.dump({"error": "pagina no disponible"}, f, ensure_ascii=False, indent=4)
        print(f"Página no disponible. Error guardado en {ruc}_error.json")
        return
    
    try:
        # Esperar a que el elemento sea visible e interactuable
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='frmBusquedaCompanias:tipoBusqueda']/tbody/tr/td[2]/label")))
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='frmBusquedaCompanias:tipoBusqueda']/tbody/tr/td[2]/label"))).click()
        
        # Ingresar el RUC
        ingresar_ruc(driver, ruc)
        
        time.sleep(3)  # Esperar un momento para que cargue el resultado

        # Intentar resolver el segundo CAPTCHA si aparece
        if manejar_captcha(driver, "//*[@id='frmCaptcha:captcha']", "//*[@id='frmCaptcha:btnPresentarContenido']/span[2]"):
            print("CAPTCHA resuelto automáticamente.")
        else:
            print("No se detectó CAPTCHA, continuando sin resolver.")

        # Esperar hasta que la página cargue los resultados
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.LINK_TEXT, "Accionistas")))
        time.sleep(4)  # Esperar un momento adicional para asegurar que todo cargue correctamente
    except Exception as e:
        print(f"Error al navegar y consultar RUC: {e}")

# EXTRACCIÓN DE INFORMACIÓN GENERAL
def extraer_informacion_general(driver):
    try:
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='frmInformacionCompanias:j_idt110:j_idt116']")))
        informacion_general = {
            "expediente": obtener_valor_elemento(driver, "//*[@id='frmInformacionCompanias:j_idt110:j_idt121']"),
            "ruc": obtener_valor_elemento(driver, "//*[@id='frmInformacionCompanias:j_idt110:j_idt126']"),
            "fecha_constitucion": obtener_valor_elemento(driver, "//*[@id='frmInformacionCompanias:j_idt110:j_idt131']"),
            "nacionalidad": obtener_valor_elemento(driver, "//*[@id='frmInformacionCompanias:j_idt110:j_idt136']"),
            "plazo_social": obtener_valor_elemento(driver, "//*[@id='frmInformacionCompanias:j_idt110:j_idt141']"),
            "oficina_control": obtener_valor_elemento(driver, "//*[@id='frmInformacionCompanias:j_idt110:j_idt146']"),
            "tipo_compania": obtener_valor_elemento(driver, "//*[@id='frmInformacionCompanias:j_idt110:j_idt151']"),
            "situacion_legal": obtener_valor_elemento(driver, "//*[@id='frmInformacionCompanias:j_idt110:j_idt156']")
        }
        return informacion_general
    except Exception as e:
        print(f"Error al extraer información general: {e}")
        return {}
    

#Para manejar errores en la Informacion General IMPORTANTE:
def obtener_valor_elemento(driver, xpath):
    try:
        elemento = WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.XPATH, xpath)))
        return elemento.get_attribute('value').strip() if elemento else ""
    except Exception as e:
        print(f"Error al extraer el valor del elemento con XPath {xpath}: {e}")
        return ""

# EXTRACCIÓN DE ACTIVIDAD ECONÓMICA
def extraer_actividad_economica(driver):
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='frmInformacionCompanias:j_idt110']/div[9]"))).click()
        time.sleep(3)
        actividad_economica = {
            "objeto_social": driver.find_element(By.XPATH, "//*[@id='frmInformacionCompanias:j_idt110:j_idt350']").text,
            "ciiu_actividad_nivel_2": driver.find_element(By.XPATH, "//*[@id='frmInformacionCompanias:j_idt110:j_idt355']").text,
            "descripcion_actividad": driver.find_element(By.XPATH, "//*[@id='frmInformacionCompanias:j_idt110:j_idt360']").text,
        }
        return actividad_economica
    except Exception as e:
        print(f"Error al extraer actividad económica: {e}")
        return {}

# EXTRACCIÓN DE ACCIONISTAS
def extraer_datos_accionistas(driver):
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='frmMenu:menuAccionistas']/span"))).click()
        if not manejar_captcha(driver, "//*[@id='frmCaptcha:captcha']", "//*[@id='frmCaptcha:btnPresentarContenido']/span[2]"):
            print("No se encontró CAPTCHA. Continuando con la extracción de datos de accionistas...")
        accionistas = []
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[@id='frmInformacionCompanias:tblAccionistas']/div[1]/table")))
        filas = driver.find_elements(By.XPATH, "//*[@id='frmInformacionCompanias:tblAccionistas']/div[1]/table/tbody/tr")
        for fila in filas:
            columnas = fila.find_elements(By.TAG_NAME, "td")
            accionista = {
                "identificacion": columnas[0].text,
                "nombre": columnas[1].text,
                "nacionalidad": columnas[2].text,
                "tipo_inversion": columnas[3].text,
                "capital": columnas[4].text,
                "restriccion": columnas[5].text
            }
            accionistas.append(accionista)
        return accionistas
    except Exception as e:
        print(f"Error al extraer datos de accionistas: {e}")
        return []

def main(ruc):
    # ruc = input("Ingresar el RUC a consultar: ")
    driver = configure_browsersupercias(headless=False) #True si no se quiere abrir el driver del chrome
    
    try:
        navegar_y_consultar_ruc(driver, ruc)
        informacion_general = extraer_informacion_general(driver)
        actividad_economica = extraer_actividad_economica(driver)
        accionistas = extraer_datos_accionistas(driver)
        
        datos_empresa = {
            "ruc": ruc,
            "informacion_general": informacion_general,
            "actividad_economica": actividad_economica,
            "accionistas": accionistas
        }
        
        with open(f'{ruc}.json', 'w', encoding='utf-8') as f:
            json.dump(datos_empresa, f, ensure_ascii=False, indent=4)
        
        print(f"Datos de la empresa extraídos y guardados en {ruc}.json")
        #input("Presiona Enter para cerrar el navegador...") #Para visualizar donde se quedo y dejar abierto el navegador
        return datos_empresa
    finally:
        driver.quit()

# if __name__ == "__main__":
#     main()
