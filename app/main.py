from flask import Flask, request, make_response, jsonify
from scripts import tables, rooms
import os

app = Flask(__name__)

@app.route('/')
def ping():
    response = make_response("pong", 200)
    response.mimetype = "text/plain"
    return response

@app.route('/run-inference', methods=['POST'])
def run_inference():
    inference_type = request.args.get('type')

    if inference_type == 'room':
        
        if 'image' not in request.files:
            return "No image file", 400
        image_file = request.files['image']
        filename = image_file.filename
        
        script_path = f'/app/scripts/rooms.py'
        temp_file_path = f'/app/temp/{filename}'
        image_file.save(temp_file_path)
        
        data_out = rooms.main(temp_file_path)
        
        return jsonify(data_out), 200
    
    elif inference_type == 'tables':
    
        if 'image' not in request.files:
            return "No image file", 400
        image_file = request.files['image']
        filename = image_file.filename
        
        script_path = f'/app/scripts/tables.py'
        temp_file_path = f'/app/temp/{filename}'
        image_file.save(temp_file_path)
        
        data_out = tables.main(temp_file_path)

        return jsonify(data_out), 200
    
    else:
        return "Unsupported inference type", 400

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    app.run(debug=True, host='0.0.0.0', port=port)
