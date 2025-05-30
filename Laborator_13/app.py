from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import timedelta

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "super-secret"  
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

jwt = JWTManager(app)

# Simulated in-memory user database
users = {
    "user1": {"password": "parola1", "role": "admin"},
    "user2": {"password": "parola2", "role": "owner"},
    "user3": {"password": "parolaX", "role": "owner"}
}


jwt_store = {}


@app.route('/auth', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = request.json.get("username", None)
    password = request.json.get("password", None)

    user = users.get(username)
    if not user or user["password"] != password:
        return jsonify({"msg": "Bad credentials"}), 401

    access_token = create_access_token(identity=username)
    jwt_store[access_token] = user["role"]

    return jsonify(access_token=access_token), 200


@app.route('/auth/jwtStore', methods=['GET'])
@jwt_required()
def validate_token():
    token = get_jwt()
    identity = get_jwt_identity()

    if identity not in users:
        return jsonify({"msg": "User not found"}), 404

    access_token = request.headers.get("Authorization", "").replace("Bearer ", "")
    role = jwt_store.get(access_token)

    if not role:
        return jsonify({"msg": "Token not found"}), 404

    return jsonify(role=role), 200


@app.route('/auth/jwtStore', methods=['DELETE'])
@jwt_required()
def logout():
    access_token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if access_token in jwt_store:
        del jwt_store[access_token]
        return jsonify({"msg": "Token invalidated"}), 200
    else:
        return jsonify({"msg": "Token not found"}), 404


@app.route('/sensor/data', methods=['GET'])
@jwt_required()
def read_sensor():
    access_token = request.headers.get("Authorization", "").replace("Bearer ", "")
    role = jwt_store.get(access_token)

    if role in ["owner", "admin"]:
        return jsonify(sensor="Temperature", value="22.5°C"), 200
    else:
        return jsonify({"msg": "Unauthorized"}), 403


@app.route('/sensor/config', methods=['POST'])
@jwt_required()
def config_sensor():
    access_token = request.headers.get("Authorization", "").replace("Bearer ", "")
    role = jwt_store.get(access_token)

    if role == "admin":
        return jsonify({"msg": "Configuration updated"}), 200
    else:
        return jsonify({"msg": "Unauthorized"}), 403

if __name__ == '__main__':
    app.run(debug=True)
