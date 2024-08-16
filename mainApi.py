from flask import Flask, request, jsonify
import mainSUPERCIASCaptcha as SC
import mainSRICaptcha as SRI

app = Flask(__name__)

@app.route('/consulta', methods=['POST'])
def process_ruc():
    # Leer los datos JSON desde el cuerpo de la solicitud
    data = request.get_json()

    # Verificar que se haya recibido la clave "ruc"
    if not data or 'ruc' not in data:
        return jsonify({"error": "Falta la clave 'ruc' en el JSON"}), 400

    # Obtener el valor de "ruc"
    ruc = data['ruc']

    # Llamar al script de Navegacion
    datos = {}
    datosSri = {}
    datos = SC.main(ruc)
    datosSri = SRI.fetch_ruc_status(ruc)
    
    datos.update(datosSri)

    response = datos

    # Devolver una respuesta en formato JSON
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(debug=True)