from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os
import json
import io
import pytz
import xlsxwriter

app = Flask(__name__, static_folder='static')
CORS(app)

# Crear carpeta de datos si no existe
if not os.path.exists('data'):
    os.makedirs('data')

# Inicializar base de datos
def init_db():
    conn = sqlite3.connect('data/bills.db')
    c = conn.cursor()
    
    # Verificar si existe la tabla
    c.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='bills'
    """)
    
    if not c.fetchone():
        # Crear tabla solo si NO existe
        c.execute('''
            CREATE TABLE bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                apellido TEXT,
                email TEXT,
                url TEXT NOT NULL,
                fecha_captura TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ Tabla bills creada")
    else:
        # Si existe, verificar y añadir columnas faltantes
        c.execute("PRAGMA table_info(bills)")
        columns = {col[1] for col in c.fetchall()}
        
        if 'nombre' not in columns:
            c.execute('ALTER TABLE bills ADD COLUMN nombre TEXT')
            print("✓ Columna 'nombre' añadida")
        if 'apellido' not in columns:
            c.execute('ALTER TABLE bills ADD COLUMN apellido TEXT')
            print("✓ Columna 'apellido' añadida")
        if 'email' not in columns:
            c.execute('ALTER TABLE bills ADD COLUMN email TEXT')
            print("✓ Columna 'email' añadida")
    
    conn.commit()
    conn.close()



# Inicializar base de datos
def init_db():
    conn = sqlite3.connect('data/bills.db')
    c = conn.cursor()
    
    # Crear tabla (DROP solo si queremos limpiar - COMENTADO)
    c.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            apellido TEXT,
            email TEXT,
            url TEXT NOT NULL,
            fecha_captura TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✓ Base de datos inicializada correctamente")

# Ejecutar al iniciar
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
        nombre = data.get('nombre', '')
        apellido = data.get('apellido', '')
        email = data.get('email', '')
        
        if not url:
            return jsonify({'success': False, 'error': 'URL no proporcionada'}), 400
        
        conn = sqlite3.connect('data/bills.db')
        c = conn.cursor()
        
        # Verificar si la URL ya existe
        c.execute('SELECT id FROM bills WHERE url = ?', (url,))
        if c.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Esta factura ya fue escaneada', 'duplicado': True}), 409
        
        # Guardar si no existe
        c.execute('''
            INSERT INTO bills (nombre, apellido, email, url, fecha_captura)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (nombre, apellido, email, url))
        
        conn.commit()
        last_id = c.lastrowid
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Factura guardada correctamente',
            'id': last_id,
            'url': url
        })
    
    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bills', methods=['GET'])
def get_bills():
    try:
        conn = sqlite3.connect('data/bills.db')
        c = conn.cursor()
        c.execute('SELECT id, nombre, apellido, email, url, fecha_captura FROM bills ORDER BY fecha_captura DESC')
        rows = c.fetchall()
        conn.close()
        
        bills = []
        for row in rows:
            bills.append({
                'id': row[0],
                'nombre': row[1],
                'apellido': row[2],
                'email': row[3],
                'url': row[4],
                'fecha_captura': row[5]
            })
        
        return jsonify(bills)
    
    except Exception as e:
        print(f'Error: {e}')
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

@app.route('/api/download/excel', methods=['GET'])
def download_excel():
    try:
        conn = sqlite3.connect('data/bills.db')
        c = conn.cursor()
        c.execute('SELECT id, nombre, apellido, email, url, fecha_captura FROM bills ORDER BY fecha_captura DESC')
        rows = c.fetchall()
        conn.close()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Facturas')

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#667eea',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        cell_format = workbook.add_format({'border': 1})
        url_format = workbook.add_format({'border': 1, 'text_wrap': True})

        # Escribir encabezados
        worksheet.write(0, 0, 'ID', header_format)
        worksheet.write(0, 1, 'Nombre', header_format)
        worksheet.write(0, 2, 'Apellido', header_format)
        worksheet.write(0, 3, 'Email', header_format)
        worksheet.write(0, 4, 'Código', header_format)
        worksheet.write(0, 5, 'Fecha Captura', header_format)
        worksheet.write(0, 6, 'URL CNMC', header_format)

        # Escribir datos
        for row_num, row in enumerate(rows, start=1):
            codigo = row[4].split('?cp=')[1].split('&')[0] if '?cp=' in row[4] else 'N/A'
            
            worksheet.write(row_num, 0, row[0], cell_format)
            worksheet.write(row_num, 1, row[1] or '-', cell_format)
            worksheet.write(row_num, 2, row[2] or '-', cell_format)
            worksheet.write(row_num, 3, row[3] or '-', cell_format)
            worksheet.write(row_num, 4, codigo, cell_format)
            worksheet.write(row_num, 5, row[5], cell_format)
            worksheet.write(row_num, 6, row[4], url_format)

        # Ajustar ancho de columnas
        worksheet.set_column(0, 0, 5)
        worksheet.set_column(1, 1, 15)
        worksheet.set_column(2, 2, 15)
        worksheet.set_column(3, 3, 25)
        worksheet.set_column(4, 4, 10)
        worksheet.set_column(5, 5, 20)
        worksheet.set_column(6, 6, 50)

        workbook.close()
        output.seek(0)

        fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"facturas_{fecha_str}.xlsx"

        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/csv', methods=['GET'])
def download_csv():
    try:
        import csv
        from io import StringIO
        
        conn = sqlite3.connect('data/bills.db')
        c = conn.cursor()
        c.execute('SELECT id, nombre, apellido, email, url, fecha_captura FROM bills ORDER BY fecha_captura DESC')
        rows = c.fetchall()
        conn.close()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Nombre', 'Apellido', 'Email', 'Código', 'Fecha Captura', 'URL CNMC'])
        
        for row in rows:
            codigo = row[4].split('?cp=')[1].split('&')[0] if '?cp=' in row[4] else 'N/A'
            writer.writerow([row[0], row[1] or '-', row[2] or '-', row[3] or '-', codigo, row[5], row[4]])
        
        output_bytes = output.getvalue().encode('utf-8-sig')
        output = io.BytesIO(output_bytes)
        
        return send_file(
            output,
            mimetype='text/csv; charset=utf-8',
            as_attachment=True,
            download_name=f'facturas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/json', methods=['GET'])
def download_json():
    try:
        conn = sqlite3.connect('data/bills.db')
        c = conn.cursor()
        c.execute('SELECT id, nombre, apellido, email, url, fecha_captura FROM bills ORDER BY fecha_captura DESC')
        rows = c.fetchall()
        conn.close()
        
        bills = []
        for row in rows:
            codigo = row[4].split('?cp=')[1].split('&')[0] if '?cp=' in row[4] else 'N/A'
            bills.append({
                'id': row[0],
                'nombre': row[1],
                'apellido': row[2],
                'email': row[3],
                'codigo': codigo,
                'url': row[4],
                'fecha_captura': row[5]
            })
        
        output = io.BytesIO(json.dumps(bills, indent=2, ensure_ascii=False).encode('utf-8'))
        
        return send_file(
            output,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'facturas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
