import os
import tempfile
import requests
import pytesseract
import cv2
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from scraping_supercias import configure_browsersupercias

#RESOLVER CAPTCHA XAVI:
def download_captcha(driver, xpath_image):
    """Descargar la imagen CAPTCHA."""
    objElement = driver.find_element(by="xpath", value=xpath_image)
    imagen_url = objElement.get_attribute("src")
    
    response = requests.get(imagen_url, verify=False)
    
    # Crear un directorio temporal
    temp_dir = tempfile.mkdtemp()
    
    # Definir la ruta del archivo en el directorio temporal
    image_path = os.path.join(temp_dir, "captcha.jpg") #ver el formato, o luego guardar
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
    print("resolver")
    """Resuelve el CAPTCHA usando los scripts de imagen."""
    image_path = download_captcha(driver, xpath_image)
    captcha_text = process_captcha(image_path)
    return captcha_text

#Web Scraping Isaac con validaciones:

def ingresar_ruc(driver, ruc):
    #Tiene que ser mas de dos, dos es lo optimo, evaluar
    retries = 2
    while retries > 0:
        try:
            input_ruc = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='frmBusquedaCompanias:parametroBusqueda_input']")))
            input_ruc.clear()
            input_ruc.click()
            time.sleep(2)  #Esperar un momento después del clic
            input_ruc.send_keys(ruc)
            time.sleep(2)  #Esperar un momento después de ingresar el RUC

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

            # Resolver el CAPTCHA automáticamente
            time.sleep(5)
            
            captcha_resuelto = resolver_captcha(driver, "//img[@id='frmBusquedaCompanias:captchaImage']")
            
            input_captcha = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='frmBusquedaCompanias:captcha']")))
            
            input_captcha.send_keys(captcha_resuelto)
            
            
            input_ruc.send_keys(Keys.RETURN) #Comentar?
            break
        except Exception as e:
            retries -= 1
            print(f"Error en ingresar_ruc: {e}. Reintentando...")
            if retries == 0:
                raise e
            
#Importante por tantos errores
def manejar_captcha(driver, xpath_captcha, xpath_boton_verificar):
    try:
        #Resolver el CAPTCHA automáticamente y verifica que este presente
        captcha_resuelto = resolver_captcha(driver, "//img[@id='frmCaptcha:captchaImage']")
        input_captcha = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, xpath_captcha)))
        input_captcha.send_keys(captcha_resuelto)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath_boton_verificar))).click()
        return True
    except Exception as e:
        print(f"No se encontró CAPTCHA: {e}")
        return False
    
def navegar_y_consultar_ruc(driver, ruc):
    driver.get('https://appscvsgen.supercias.gob.ec/consultaCompanias/societario/busquedaCompanias.jsf')
    
    try:
        #Esperar a que el elemento sea visible e interactuable
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='frmBusquedaCompanias:tipoBusqueda']/tbody/tr/td[2]/label")))
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='frmBusquedaCompanias:tipoBusqueda']/tbody/tr/td[2]/label"))).click()
        
        #Ingresar el RUC
        ingresar_ruc(driver, ruc)
        
        time.sleep(3)  # Esperar un momento para que cargue el resultado
        
        #Manejar CAPTCHA (esto es un lugar donde necesitarás adaptar a tu solución de CAPTCHA)
        #En este ejemplo se asume que el usuario ingresará el CAPTCHA manualmente.
        #captcha_resuelto = input("Ingrese el CAPTCHA mostrado: ")
        #input_captcha = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='frmBusquedaCompanias:captcha']")))
        #input_captcha.send_keys(captcha_resuelto)
        
        #Hacer clic en el botón "Consultar"
        driver.find_element(By.XPATH, "//*[@id='frmBusquedaCompanias:btnConsultarCompania']/span[2]").click()
        
        #Esperar hasta que la página cargue los resultados
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.LINK_TEXT, "Accionistas")))
        time.sleep(4)  # Esperar un momento adicional para asegurar que todo cargue correctamente
    except Exception as e:
        print(f"Error al navegar y consultar RUC: {e}")

#Informacion General Primera Pantalla
def extraer_informacion_general(driver):
    try:
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//*[@id='frmInformacionCompanias:j_idt110:j_idt116']")))
        #time.sleep(5)
        informacion_general = {
            "expediente": obtener_valor_elemento(driver, "//*[@id='frmInformacionCompanias:j_idt110:j_idt121']"),
            "ruc": obtener_valor_elemento(driver, "//*[@id='frmInformacionCompanias:j_idt110:j_idt126']"),
            "fecha_constitucion": obtener_valor_elemento(driver, "//*[@id='frmInformacionCompanias:j_idt110:j_idt131']"),
            "nacionalidad": obtener_valor_elemento(driver, "//*[@id='frmInformacionCompanias:j_idt110:j_idt136']"),
            "plazo_social": obtener_valor_elemento(driver, "//*[@id='frmInformacionCompanias:j_idt110:j_idt141']"),
            "oficina_control": obtener_valor_elemento(driver, "//*[@id='frmInformacionCompanias:j_idt110:j_idt146']"),
            #"expediente": obtener_valor_elemento(driver, "/html/body/div[3]/div/form/span[1]/div/div/table[2]/tbody/tr[2]/td/div/div[2]/table/tbody/tr[1]/td[2]/input"),
            #"ruc": obtener_valor_elemento(driver, "/html/body/div[3]/div/form/span[1]/div/div/table[2]/tbody/tr[2]/td/div/div[2]/table/tbody/tr[1]/td[5]/input"),
            #"fecha_constitucion": obtener_valor_elemento(driver, "/html/body/div[3]/div/form/span[1]/div/div/table[2]/tbody/tr[2]/td/div/div[2]/table/tbody/tr[1]/td[8]/input"),
            #"nacionalidad": obtener_valor_elemento(driver, "/html/body/div[3]/div/form/span[1]/div/div/table[2]/tbody/tr[2]/td/div/div[2]/table/tbody/tr[2]/td[2]/input"),
            #"plazo_social": obtener_valor_elemento(driver, "/html/body/div[3]/div/form/span[1]/div/div/table[2]/tbody/tr[2]/td/div/div[2]/table/tbody/tr[2]/td[5]/input"),
            #"oficina_control": obtener_valor_elemento(driver, "/html/body/div[3]/div/form/span[1]/div/div/table[2]/tbody/tr[2]/td/div/div[2]/table/tbody/tr[2]/td[8]/input"),
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
    
#Actividad Economica Primera Pantalla
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
    

#Accionistas de la Compañia Segunda Pantalla
def extraer_datos_accionistas(driver):
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='frmMenu:menuAccionistas']/span"))).click()
        if not manejar_captcha(driver, "//*[@id='frmCaptcha:captcha']", "//*[@id='frmCaptcha:btnPresentarContenido']/span[2]"):
            print("No se encontró CAPTCHA. Continuando con la extracción de datos de accionistas...")
        #time.sleep(5)
        accionistas = []
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[@id='frmInformacionCompanias:tblAccionistas']/div[1]/table")))
        accionistas = []
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
    #ruc = input("Ingresar el RUC a consultar: ")
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
        return(datos_empresa)
        #input("Presiona Enter para cerrar el navegador...") #Para visualizar donde se quedo y dejar abierto el navegador
    finally:
        driver.quit()

#if __name__ == "__main__":
#    main()
#print(main("1791754689001"))