from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os
import json

app = Flask(__name__, static_folder='static')
CORS(app)

# Crear carpeta de datos si no existe
if not os.path.exists('data'):
    os.makedirs('data')

# Inicializar base de datos
def init_db():
    conn = sqlite3.connect('data/bills.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            fecha_captura TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('app_publica.html')

@app.route('/admin')
def admin():
    return render_template('admin_panel.html')

@app.route('/api/scrape', methods=['POST'])
def scrape():
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL no proporcionada'}), 400
        
        # Guardar en BD
        conn = sqlite3.connect('data/bills.db')
        c = conn.cursor()
        c.execute('INSERT INTO bills (url) VALUES (?)', (url,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Factura guardada correctamente'})
    
    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bills', methods=['GET'])
def get_bills():
    try:
        conn = sqlite3.connect('data/bills.db')
        c = conn.cursor()
        c.execute('SELECT id, url, fecha_captura FROM bills ORDER BY fecha_captura DESC')
        rows = c.fetchall()
        conn.close()
        
        bills = []
        for row in rows:
            bills.append({
                'id': row[0],
                'url': row[1],
                'fecha_captura': row[2]
            })
        
        return jsonify(bills)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bills/<int:bill_id>', methods=['DELETE'])
def delete_bill(bill_id):
    try:
        conn = sqlite3.connect('data/bills.db')
        c = conn.cursor()
        c.execute('DELETE FROM bills WHERE id = ?', (bill_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bills', methods=['DELETE'])
def delete_all_bills():
    try:
        conn = sqlite3.connect('data/bills.db')
        c = conn.cursor()
        c.execute('DELETE FROM bills')
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
