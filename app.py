import os
import qrcode
import io
import base64
from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app)

# Store active connections
connections = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mobile/<string:room_id>')
def mobile(room_id):
    return render_template('mobile.html', room_id=room_id)

@app.route('/generate_qr')
def generate_qr():
    print("Generate QR route called")
    room_id = str(uuid.uuid4())
    print(f"Generated room_id: {room_id}")
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr_data = f"{request.host_url}mobile/{room_id}"
    print(f"QR code data: {qr_data}")
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    print("QR code image generated")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    print(f"QR code image encoded, length: {len(img_str)}")
    
    response_data = {'qr_code': img_str, 'room_id': room_id}
    print("Returning QR code data")
    return jsonify(response_data)

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    connections[room] = request.sid
    emit('joined', {'room': room}, room=room)
    print(f"Client joined room: {room}")

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)
    connections.pop(room, None)
    emit('left', {'room': room}, room=room)
    print(f"Client left room: {room}")

@socketio.on('file_transfer')
def handle_file_transfer(data):
    room = data['room']
    file_data = data['file_data']
    file_name = data['file_name']
    from_device = data['from']
    
    if room in connections:
        emit('file_received', {'file_data': file_data, 'file_name': file_name, 'from': from_device}, room=room)
        print(f"File transferred: {file_name} from {from_device} in room {room}")

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    print("Starting Flask application")
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
