from flask import Flask, render_template, request, jsonify
from database import get_db_connections
from datetime import datetime

app = Flask(__name__)
db_dynamo, cache_keydb = get_db_connections()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/votar', methods=['POST'])
def registrar_voto():
    """
    Procesa votos masivos mitigando cuellos de botella mediante Memurai
    y asegurando persistencia en DynamoDB.
    """
    try:
        ci = request.form.get('voter_id')
        candidato = request.form.get('candidate')
        tipo_eleccion = request.form.get('eleccion_tipo') # PRESIDENTE | GOBERNADOR

        # 1. Seguridad: Validación de Identidad y Rol en Memurai (HSET ciudadano:{CI})
        user_data = cache_keydb.hgetall(f"ciudadano:{ci}")
        if not user_data:
            return jsonify({"status": "error", "message": "CI no registrado en el padrón."}), 404

        # 2. Integridad: Control de Doble Voto (SADD padron:ha_votado:{TIPO})
        es_nuevo = cache_keydb.sadd(f"padron:ha_votado:{tipo_eleccion}", ci)
        if not es_nuevo:
            return jsonify({"status": "error", "message": f"Ya emitió su voto para {tipo_eleccion}."}), 403

        # 3. Disponibilidad: Conteo Atómico en Real-Time (Redis INCR)
        cache_keydb.incr(f"votos:{tipo_eleccion}:total:partido:{candidato}")
        cache_keydb.incr(f"votos:{tipo_eleccion}:total:tipo:valido")

        # 4. Persistencia: Auditoría en DynamoDB (Single Table Design)
        table = db_dynamo.Table('Votacion_Escrutinio')
        table.put_item(
            Item={
                'PK': f'CI#{ci}',
                'SK': f'ELEC#{tipo_eleccion}',
                'candidato': candidato,
                'mesa': user_data.get('mesa_asignada', 'SIN_MESA'),
                'timestamp': datetime.now().isoformat(),
                'voto_id': f"{ci}-{tipo_eleccion}"
            }
        )

        return jsonify({"status": "success", "message": f"Voto para {tipo_eleccion} procesado."}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": "Fallo en la infraestructura: " + str(e)}), 500

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/resultados/<eleccion>')
def obtener_resultados(eleccion):
    try:
        partidos = ["A", "B"] if eleccion == "PRESIDENTE" else ["X", "Y"]
        resultados = {}
        
        for p in partidos:
            valor = cache_keydb.get(f"votos:{eleccion}:total:partido:{p}")
            # Si la llave no existe en Memurai, la inicializamos en 0
            if valor is None:
                cache_keydb.set(f"votos:{eleccion}:total:partido:{p}", 0)
                valor = 0
            resultados[f"Partido_{p}"] = int(valor)

        total = cache_keydb.get(f"votos:{eleccion}:total:tipo:valido")
        resultados["Total"] = int(total or 0)
        
        return jsonify(resultados)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)