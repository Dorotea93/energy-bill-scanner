﻿from flask import Flask, render_template, request, jsonify, send_file
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
        
        # Extraer información
        info = extract_info_from_url(url)
        
        # Guardar en BD
        conn = sqlite3.connect('data/bills.db')
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO bills (
                url, codigo_postal, periodo, tarifa, precio, 
                energia_verde, permanencia, revision, servicios,
                comercializadora, fecha_captura
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            info.get('url'),
            info.get('codigo_postal', 'N/A'),
            info.get('periodo', 'N/A'),
            info.get('tarifa', 'N/A'),
            info.get('precio', 0),
            info.get('energia_verde', 'No'),
            info.get('permanencia', 'N/A'),
            info.get('revision', 'N/A'),
            info.get('servicios', 'N/A'),
            info.get('comercializadora', 'N/A'),
            info.get('fecha_captura', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Factura guardada correctamente', 'data': info})
    
    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download/csv', methods=['GET'])
def download_csv():
    try:
        import csv
        from io import StringIO
        
        conn = sqlite3.connect('data/bills.db')
        c = conn.cursor()
        c.execute('SELECT * FROM bills ORDER BY id DESC')
        bills = c.fetchall()
        conn.close()
        
        # Crear CSV en memoria
        output = StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        headers = ['ID', 'Comercializadora', 'Periodo', 'Tarifa', 'Precio (€)', 
                   'Energía Verde', 'Permanencia', 'Revisión', 'Servicios', 
                   'Código Postal', 'Fecha Captura', 'URL']
        writer.writerow(headers)
        
        # Datos
        for bill in bills:
            row = [
                bill[0],  # ID
                bill[11] if len(bill) > 11 else 'N/A',  # Comercializadora
                bill[2] if len(bill) > 2 else 'N/A',  # Periodo
                bill[3] if len(bill) > 3 else 'N/A',  # Tarifa
                bill[4] if len(bill) > 4 else 0,  # Precio
                bill[5] if len(bill) > 5 else 'No',  # Energía verde
                bill[6] if len(bill) > 6 else 'N/A',  # Permanencia
                bill[7] if len(bill) > 7 else 'N/A',  # Revisión
                bill[8] if len(bill) > 8 else 'N/A',  # Servicios
                bill[1] if len(bill) > 1 else 'N/A',  # Código postal
                bill[10] if len(bill) > 10 else 'N/A',  # Fecha captura
                bill[9] if len(bill) > 9 else 'N/A'  # URL
            ]
            writer.writerow(row)
        
        # Convertir a bytes
        output_bytes = output.getvalue().encode('utf-8-sig')  # UTF-8 con BOM para Excel
        from io import BytesIO
        output = BytesIO(output_bytes)
        
        return send_file(
            output,
            mimetype='text/csv; charset=utf-8',
            as_attachment=True,
            download_name=f'facturas_energia_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    
    except Exception as e:
        print(f'Error generando CSV: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500



def extract_info_from_url(url):
    """Extrae información de la URL del QR"""
    try:
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        
        # Extrae parámetros de la URL
        info = {
            'url': url,
            'codigo': params.get('cp', ['N/A'])[0],
            'fecha_captura': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f'Información extraída: {info}')
        return info
    except Exception as e:
        print(f'Error extrayendo info: {e}')
        return {'url': url, 'error': str(e)}


def extract_info_from_url(url):
    """Extrae información detallada de la URL del QR mediante web scraping"""
    try:
        import urllib.parse
        from bs4 import BeautifulSoup
        import requests
        
        # Parsear parámetros de la URL
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        
        # Extraer datos básicos de la URL
        codigo_postal = params.get('cp', ['N/A'])[0]
        precio = params.get('imp', ['N/A'])[0]
        energia_inicio = params.get('iniF', ['N/A'])[0]
        energia_fin = params.get('finF', ['N/A'])[0]
        
        # Convertir fechas a formato legible
        try:
            fecha_inicio = datetime.strptime(energia_inicio, '%Y-%m-%d').strftime('%d/%m/%Y') if energia_inicio != 'N/A' else 'N/A'
            fecha_fin = datetime.strptime(energia_fin, '%Y-%m-%d').strftime('%d/%m/%Y') if energia_fin != 'N/A' else 'N/A'
            periodo = f"{fecha_inicio} - {fecha_fin}"
        except:
            periodo = 'N/A'
        
        # Intentar extraer datos adicionales
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar elementos en la página
            comercializadora = 'N/A'
            tarifa = 'N/A'
            energia_verde = 'No'
            permanencia = 'N/A'
            revision = 'N/A'
            servicios = 'N/A'
            
            # Extraer texto visible
            texto_pagina = soup.get_text().lower()
            
            # Detectar información de la página
            if 'energía verde' in texto_pagina or 'energía 100% renovable' in texto_pagina:
                energia_verde = 'Sí'
            
            if 'sin permanencia' in texto_pagina:
                permanencia = 'Sin permanencia'
            elif 'permanencia' in texto_pagina:
                permanencia = 'Con permanencia'
            
            if 'revisión anual' in texto_pagina:
                revision = 'Revisión anual'
            elif 'revisión mensual' in texto_pagina:
                revision = 'Revisión mensual'
            elif 'sin revisión' in texto_pagina:
                revision = 'Sin revisión'
            
            if 'servicios adicionales' in texto_pagina:
                servicios = 'Con servicios'
            elif 'sin servicios' in texto_pagina:
                servicios = 'Sin servicios'
            
            # Buscar tipo de tarifa (PVP, PVPC, fijo, variable)
            if '1 precio fijo' in texto_pagina or 'precio fijo' in texto_pagina:
                tarifa = 'Tarifa con 1 precio fijo'
            elif '2 precios fijos' in texto_pagina or '2 tramos' in texto_pagina:
                tarifa = 'Tarifa con 2 precios fijos'
            elif '3 precios fijos' in texto_pagina or '3 tramos' in texto_pagina:
                tarifa = 'Tarifa con 3 precios fijos'
            elif 'pvpc' in texto_pagina:
                tarifa = 'PVPC'
            elif 'pvp' in texto_pagina:
                tarifa = 'PVP'
            
            # Intentar encontrar comercializadora
            h1_elements = soup.find_all('h1')
            for h1 in h1_elements:
                if h1.text.strip():
                    comercializadora = h1.text.strip()[:100]
                    break
            
        except Exception as e:
            print(f'Error en web scraping: {e}')
        
        tz = pytz.timezone('Europe/Madrid')
        fecha_local = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
        
        info = {
            'url': url,
            'codigo_postal': codigo_postal,
            'periodo': periodo,
            'tarifa': tarifa,
            'precio': float(precio) if precio != 'N/A' else 0,
            'energia_verde': energia_verde,
            'permanencia': permanencia,
            'revision': revision,
            'servicios': servicios,
            'comercializadora': comercializadora,
            'fecha_captura': fecha_local
        }
        
        print(f'Información extraída: {info}')
        return info
    
    except Exception as e:
        print(f'Error extrayendo info: {e}')
        return {
            'url': url,
            'error': str(e),
            'fecha_captura': datetime.now(pytz.timezone('Europe/Madrid')).strftime('%Y-%m-%d %H:%M:%S')
        }


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