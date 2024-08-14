from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import json
from scraping_sri import configure_browser

def fetch_ruc_status(ruc_number):
    url = "https://srienlinea.sri.gob.ec/sri-en-linea/SriRucWeb/ConsultaRuc/Consultas/consultaRuc"
    driver = configure_browser(headless=False)  # Cambiar a True para NO ver el navegador

    try:
        # Verificar si la página está disponible
        driver.set_page_load_timeout(10)
        driver.get(url)
    except Exception as e:
        print("Página no disponible.")
        return {"error": "Página no disponible"}

    try:
        # Esperar hasta que el campo de RUC esté presente
        ruc_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="busquedaRucId"]'))
        )
        print("Campo RUC encontrado")
        
        # Ingresar el número de RUC
        ruc_input.send_keys(ruc_number)

        # Salir del campo de RUC para que se valide
        ruc_input.send_keys(Keys.TAB)

        # Esperar unos segundos para que el botón se habilite
        time.sleep(3)
        
        # Esperar hasta que el botón de consulta esté habilitado
        consult_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="sribody"]/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[1]/div[6]/div[2]/div/div[2]/div/button/span[1]'))
        )
        print("Botón de consultar habilitado")

        # Click en el botón de consulta
        consult_button.click()
        print("Botón de consultar clickeado")

        # Verificar si aparece un CAPTCHA
        try:
            captcha_present = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="rc-imageselect"]'))
            )
            print("CAPTCHA detectado, esperando a que sea resuelto...")
            # Esperar un tiempo prudente para que el CAPTCHA sea resuelto
            time.sleep(10)  # Ajusta según el tiempo promedio de resolución
        except Exception as e:
            print("No se detectó CAPTCHA, continuando...")

        # Esperar hasta que la página de resultados se cargue y contenga el estado del contribuyente
        status_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="sribody"]/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[1]/sri-mostrar-contribuyente/div[1]/div[4]/div/div[1]/div[2]/div/span'))
        )
        print("Estado del contribuyente encontrado")
        

        # Añadir un tiempo de espera adicional importante
        time.sleep(4)  # Esperar 4 segundos para asegurarse de que la tabla esté completamente cargada


        # Extraer datos en JSON
        data = {
            "RUC": ruc_number,
            "Estado_contribuyente": status_element.text,
            "Razon_social": driver.find_element(By.XPATH, '//*[@id="sribody"]/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[1]/sri-mostrar-contribuyente/div[1]/div[2]/div[2]/div/span').text,
            "Representante_legal": {
                "Razon_social": driver.find_element(By.XPATH, '//*[@id="sribody"]/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[1]/sri-mostrar-contribuyente/div[1]/div[4]/div/div[2]/span/div/div[2]/div/div[2]/div/div[2]').text,
                "Identificacion": driver.find_element(By.XPATH, '//*[@id="sribody"]/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[1]/sri-mostrar-contribuyente/div[1]/div[4]/div/div[2]/span/div/div[2]/div/div[2]/div/div[4]').text
            },
            "Actividad_economica_principal": driver.find_element(By.XPATH, '//*[@id="sribody"]/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[1]/sri-mostrar-contribuyente/div[4]/div/div[1]/div[2]/table/tbody/tr/td').text,
            "Informacion_adicional": {
                "Tipo_contribuyente": driver.find_element(By.XPATH, '//*[@id="sribody"]/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[1]/sri-mostrar-contribuyente/div[4]/div/div[4]/div/table/tbody/tr/td[1]').text,
                "Regimen": driver.find_element(By.XPATH, '//*[@id="sribody"]/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[1]/sri-mostrar-contribuyente/div[4]/div/div[4]/div/table/tbody/tr/td[2]').text,
                "Categoria": driver.find_element(By.XPATH, '//*[@id="sribody"]/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[1]/sri-mostrar-contribuyente/div[4]/div/div[4]/div/table/tbody/tr/td[3]').text,
                "Obligado_a_llevar_contabilidad": driver.find_element(By.XPATH, '//*[@id="sribody"]/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[1]/sri-mostrar-contribuyente/div[4]/div/div[7]/div/table/tbody/tr/td[1]').text,
                "Agente_de_retencion": driver.find_element(By.XPATH, '/html/body/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[1]/sri-mostrar-contribuyente/div[4]/div/div[7]/div/table/tbody/tr/td[2]').text,
                "Contribuyente_especial": driver.find_element(By.XPATH, '//*[@id="sribody"]/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[1]/sri-mostrar-contribuyente/div[4]/div/div[7]/div/table/tbody/tr/td[3]').text,
                "Fecha_inicio_actividades": driver.find_element(By.XPATH, '/html/body/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[1]/sri-mostrar-contribuyente/div[4]/div/div[10]/div/table/tbody/tr/td[1]').text,
                "Fecha_actualizacion": driver.find_element(By.XPATH, '//*[@id="sribody"]/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[1]/sri-mostrar-contribuyente/div[4]/div/div[10]/div/table/tbody/tr/td[2]').text,
                "Fecha_cese_actividades": driver.find_element(By.XPATH, '//*[@id="sribody"]/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[1]/sri-mostrar-contribuyente/div[4]/div/div[10]/div/table/tbody/tr/td[3]').text,
                "Fecha_reinicio_actividades": driver.find_element(By.XPATH, '//*[@id="sribody"]/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[1]/sri-mostrar-contribuyente/div[4]/div/div[10]/div/table/tbody/tr/td[4]').text
            }
        }

        # Hacer clic en el botón de "Mostrar establecimiento"
        show_establishment_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="sribody"]/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[3]/div[1]/div[2]/div/div[4]/button/span[1]'))
        )
        show_establishment_button.click()

        # Añadir un tiempo de espera adicional importante
        time.sleep(4)  # Esperar 4 segundos para asegurarse de que la tabla esté completamente cargada

        # Esperar y obtener los datos de la tabla de establecimiento
        establishment_data = {
            "No_establecimiento": driver.find_element(By.XPATH, '//*[@id="sribody"]/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[3]/div[2]/div/div/div[3]/sri-listar-establecimientos/div[4]/div/p-datatable/div/div[2]/table/tbody/tr/td[1]/span[2]').text,
            "Nombre_comercial": driver.find_element(By.XPATH, '//*[@id="sribody"]/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[3]/div[2]/div/div/div[3]/sri-listar-establecimientos/div[4]/div/p-datatable/div/div[2]/table/tbody/tr/td[2]/span[2]').text,
            "Ubicacion_establecimiento": driver.find_element(By.XPATH, '//*[@id="sribody"]/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[3]/div[2]/div/div/div[3]/sri-listar-establecimientos/div[4]/div/p-datatable/div/div[2]/table/tbody/tr/td[3]/span[2]').text,
            "Estado_establecimiento": driver.find_element(By.XPATH, '//*[@id="sribody"]/sri-root/div/div[2]/div/div/sri-consulta-ruc-web-app/div/sri-ruta-ruc/div[2]/div[3]/div[2]/div/div/div[3]/sri-listar-establecimientos/div[4]/div/p-datatable/div/div[2]/table/tbody/tr/td[4]/span[2]').text
        }

        data["Establecimiento_matriz"] = establishment_data

    except Exception as e:
        print(f"Error durante el scraping: {e}")
        data = {"error": "No se pudo obtener los datos del contribuyente."}
    finally:
        # Cerrar el navegador:
        driver.quit()

    return data

# if __name__ == "__main__":
#     ruc_number = input("Por favor, ingresar el número de RUC: ")  # Solicita el número de RUC al usuario
#     data = fetch_ruc_status(ruc_number)
    
#     if data:
#         with open(f"{ruc_number}_data.json", "w", encoding="utf-8") as json_file:
#             json.dump(data, json_file, ensure_ascii=False, indent=4)
#         print(f"Los datos han sido guardados en {ruc_number}_data.json")
#     else:
#         print("No se pudo obtener los datos del contribuyente.")
