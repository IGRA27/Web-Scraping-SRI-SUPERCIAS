from flask import Flask, request, jsonify
import mainSUPERCIASCaptcha as SC
import mainSRICaptcha as SRI

app = Flask(__name__)

@app.route('/consulta', methods=['POST'])
def process_cedula():
    # Leer los datos JSON desde el cuerpo de la solicitud
    data = request.get_json()

    # Verificar que se haya recibido la clave "cedula"
    if not data or 'cedula' not in data:
        return jsonify({"error": "Falta la clave 'cedula' en el JSON"}), 400

    # Obtener el valor de "cedula"
    cedula = data['cedula']

    # Llamar al script de Navegacion
    datos = {}
    datosSri = {}
    datos = SC.main(cedula)
    datosSri = SRI.fetch_ruc_status(cedula)
    
    datos.update(datosSri)

    response = datos

    # Devolver una respuesta en formato JSON
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(debug=True)