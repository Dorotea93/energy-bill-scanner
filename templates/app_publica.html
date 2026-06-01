from flask import Flask, render_template, request, jsonify, send_file, session
from flask_cors import CORS
import sqlite3
from datetime import datetime
import os
import json
import io
import pytz
import xlsxwriter
import hashlib
import secrets
from email_validator import validate_email, EmailNotValidError
from urllib.parse import urlparse, parse_qs
import logging

app = Flask(__name__, static_folder='static')
CORS(app)

# 🔐 Configuración de seguridad
app.secret_key = secrets.token_hex(32)
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')  # Cambiar en producción
TIMEZONE = pytz.timezone('Europe/Madrid')

# 📝 Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear carpeta de datos si no existe
if not os.path.exists('data'):
    os.makedirs('data')


def init_db():
    """Inicializa la base de datos con todas las tablas necesarias"""
    conn = sqlite3.connect('data/bills.db')
    c = conn.cursor()

    c.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='bills'
    """)
    existe = c.fetchone()

    if not existe:
        c.execute('''
            CREATE TABLE bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellidos TEXT NOT NULL,
                email TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                codigo TEXT,
                fecha_captura TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('CREATE INDEX idx_email ON bills(email)')
        c.execute('CREATE INDEX idx_nombre ON bills(nombre)')
        c.execute('CREATE INDEX idx_fecha ON bills(fecha_captura DESC)')
        logger.info("✓ Tabla bills creada con índices")
    else:
        c.execute("PRAGMA table_info(bills)")
        columnas = {col[1] for col in c.fetchall()}
        
        if 'codigo' not in columnas:
            c.execute('ALTER TABLE bills ADD COLUMN codigo TEXT')
            logger.info("✓ Columna 'codigo' añadida")

    conn.commit()
    conn.close()
    logger.info("✓ Base de datos inicializada correctamente")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def validar_email(email):
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False


def validar_url_cnmc(url):
    """Valida de forma infalible si la URL es de la CNMC (inmune a falta de http/https y mayúsculas)"""
    if not url:
        return False
    try:
        # Analizamos el texto en minúsculas y limpio de espacios
        url_lower = url.strip().lower()
        
        # Comprobación de seguridad por palabras clave del dominio oficial
        tiene_dominio = ('cnmc.gob.es' in url_lower) or ('comparador' in url_lower)
        
        # Comprobación de formato (factura clásica '?cp=' o nueva factura '/listado/')
        tiene_formato = ('cp=' in url_lower) or ('listado' in url_lower)
        
        if tiene_dominio and tiene_formato:
            return True
            
        return False
    except:
        return False


def extraer_codigo_qr(url):
    """Extrae el código identificador de la factura de forma segura"""
    try:
        url_clean = url.strip()
        # Asegurar protocolo para no romper urlparse en la extracción
        if not url_clean.lower().startswith(('http://', 'https://')):
            url_clean = 'https://' + url_clean
            
        parsed = urlparse(url_clean)
        params = parse_qs(parsed.query)
        
        # Formato clásico ?cp=
        codigo = None
        for k, v in params.items():
            if k.lower() == 'cp':
                codigo = v[0]
                break
                
        # Formato nuevo /listado/ hash largo
        if not codigo and 'listado' in parsed.path.lower():
            path_parts = parsed.path.split('/')
            for i, part in enumerate(path_parts):
                if part.lower() == 'listado' and i + 1 < len(path_parts):
                    # Extraemos los primeros 15 caracteres del hash para el Excel
                    codigo = path_parts[i+1][:15] + "..."
                    break
                    
        return codigo if codigo else 'N/A'
    except Exception as e:
        logger.error(f"Error extrayendo código: {e}")
        return 'N/A'


def get_db_connection():
    conn = sqlite3.connect('data/bills.db')
    conn.row_factory = sqlite3.Row
    return conn


init_db()


# ==================== AUTENTICACIÓN ====================

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        password = data.get('password', '')
        
        if hash_password(password) == hash_password(ADMIN_PASSWORD):
            session['authenticated'] = True
            session.permanent = True
            return jsonify({'success': True, 'message': 'Autenticado correctamente'})
        else:
            return jsonify({'success': False, 'error': 'Contraseña incorrecta'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


@app.route('/api/auth/check', methods=['GET'])
def check_auth():
    return jsonify({'authenticated': session.get('authenticated', False)})


def require_auth(f):
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'error': 'No autenticado'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


# ==================== RUTAS PÚBLICAS ====================

@app.route('/')
def index():
    return render_template('app_publica.html')


@app.route('/admin')
def admin():
    return render_template('admin_panel.html')


@app.route('/api/check-qr', methods=['POST'])
def check_qr():
    try:
        data = request.json
        url = data.get('url', '').strip()

        if not url:
            return jsonify({'success': False, 'error': 'URL no proporcionada'}), 400

        if not validar_url_cnmc(url):
            return jsonify({'success': False, 'error': 'URL no válida para el comparador CNMC'}), 400

        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT id FROM bills WHERE url = ?', (url,))
        existe = c.fetchone()
        conn.close()

        if existe:
            return jsonify({'existe': True, 'id': existe['id']})
        else:
            return jsonify({'existe': False})

    except Exception as e:
        logger.error(f'Error en /api/check-qr: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/scrape', methods=['POST'])
def scrape():
    try:
        data = request.json
        url = data.get('url', '').strip()
        nombre = data.get('nombre', '').strip()
        apellidos = data.get('apellidos', '').strip()
        email = data.get('email', '').strip()

        if not url or not nombre or not apellidos or not email:
            return jsonify({'success': False, 'error': 'Faltan datos requeridos'}), 400

        if not validar_email(email):
            return jsonify({'success': False, 'error': 'Email no válido'}), 400

        if not validar_url_cnmc(url):
            return jsonify({'success': False, 'error': 'URL no válida'}), 400

        nombre = nombre[:100]
        apellidos = apellidos[:100]
        email = email[:255]

        conn = get_db_connection()
        c = conn.cursor()

        c.execute('SELECT id FROM bills WHERE url = ?', (url,))
        if c.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Esta factura ya fue escaneada',
                'duplicado': True
            }), 409

        codigo = extraer_codigo_qr(url)
        fecha_captura = datetime.now(TIMEZONE).isoformat()
        
        c.execute('''
            INSERT INTO bills (nombre, apellidos, email, url, codigo, fecha_captura)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (nombre, apellidos, email, url, codigo, fecha_captura))

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
        logger.error(f'Error en /api/scrape: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== RUTAS PROTEGIDAS (ADMIN) ====================

@app.route('/api/bills', methods=['GET'])
@require_auth
def get_bills():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        search = request.args.get('search', '').strip()
        
        page = max(1, page)
        limit = min(limit, 100)
        offset = (page - 1) * limit

        conn = get_db_connection()
        c = conn.cursor()

        query = 'SELECT id, nombre, apellidos, email, url, codigo, fecha_captura FROM bills'
        params = []

        if search:
            query += ' WHERE nombre LIKE ? OR apellidos LIKE ? OR email LIKE ? OR codigo LIKE ?'
            search_param = f'%{search}%'
            params = [search_param, search_param, search_param, search_param]

        count_query = f'SELECT COUNT(*) as total FROM ({query})'
        total = c.execute(count_query, params).fetchone()['total']

        query += ' ORDER BY fecha_captura DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])

        rows = c.execute(query, params).fetchall()
        conn.close()

        bills = []
        for row in rows:
            bills.append({
                'id': row['id'],
                'nombre': row['nombre'],
                'apellidos': row['apellidos'],
                'email': row['email'],
                'url': row['url'],
                'codigo': row['codigo'],
                'fecha_captura': row['fecha_captura']
            })

        return jsonify({
            'bills': bills,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/bills/<int:bill_id>', methods=['DELETE'])
@require_auth
def delete_bill(bill_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM bills WHERE id = ?', (bill_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/bills', methods=['DELETE'])
@require_auth
def delete_all_bills():
    try:
        confirmation = request.json.get('confirmation') if request.json else None
        if confirmation != 'DELETE_ALL_BILLS':
            return jsonify({'error': 'Confirmación requerida'}), 400

        conn = get_db_connection()
        c = conn.cursor()
        count = c.execute('SELECT COUNT(*) as total FROM bills').fetchone()['total']
        c.execute('DELETE FROM bills')
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'deleted': count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== EXPORTACIONES ====================

@app.route('/api/download/excel', methods=['GET'])
@require_auth
def download_excel():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT id, nombre, apellidos, email, codigo, fecha_captura, url FROM bills ORDER BY fecha_captura DESC')
        rows = c.fetchall()
        conn.close()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Facturas')

        header_format = workbook.add_format({'bold': True, 'bg_color': '#667eea', 'font_color': 'white', 'border': 1, 'align': 'center'})
        cell_format = workbook.add_format({'border': 1})
        url_format = workbook.add_format({'border': 1, 'text_wrap': True})
        date_format = workbook.add_format({'border': 1, 'num_format': 'yyyy-mm-dd hh:mm:ss'})

        headers = ['ID', 'Nombre', 'Apellidos', 'Email', 'Código', 'Fecha Captura', 'URL CNMC']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)

        for row_num, row in enumerate(rows, start=1):
            worksheet.write(row_num, 0, row['id'], cell_format)
            worksheet.write(row_num, 1, row['nombre'] or '-', cell_format)
            worksheet.write(row_num, 2, row['apellidos'] or '-', cell_format)
            worksheet.write(row_num, 3, row['email'] or '-', cell_format)
            worksheet.write(row_num, 4, row['codigo'] or '-', cell_format)
            worksheet.write(row_num, 5, row['fecha_captura'], date_format)
            worksheet.write(row_num, 6, row['url'], url_format)

        worksheet.set_column(0, 0, 5)
        worksheet.set_column(1, 3, 20)
        worksheet.set_column(4, 4, 12)
        worksheet.set_column(5, 5, 20)
        worksheet.set_column(6, 6, 50)

        workbook.close()
        output.seek(0)

        return send_file(output, as_attachment=True, download_name=f"facturas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/csv', methods=['GET'])
@require_auth
def download_csv():
    try:
        import csv
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT id, nombre, apellidos, email, codigo, fecha_captura, url FROM bills ORDER BY fecha_captura DESC')
        rows = c.fetchall()
        conn.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Nombre', 'Apellidos', 'Email', 'Código', 'Fecha Captura', 'URL CNMC'])

        for row in rows:
            writer.writerow([row['id'], row['nombre'] or '-', row['apellidos'] or '-', row['email'] or '-', row['codigo'] or '-', row['fecha_captura'], row['url']])

        output_bytes = output.getvalue().encode('utf-8-sig')
        output = io.BytesIO(output_bytes)

        return send_file(output, mimetype='text/csv', as_attachment=True, download_name=f"facturas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/json', methods=['GET'])
@require_auth
def download_json():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT id, nombre, apellidos, email, codigo, fecha_captura, url FROM bills ORDER BY fecha_captura DESC')
        rows = c.fetchall()
        conn.close()

        bills = []
        for row in rows:
            bills.append({'id': row['id'], 'nombre': row['nombre'], 'apellidos': row['apellidos'], 'email': row['email'], 'codigo': row['codigo'], 'url': row['url'], 'fecha_captura': row['fecha_captura']})

        output = io.BytesIO(json.dumps(bills, indent=2, ensure_ascii=False).encode('utf-8'))
        return send_file(output, mimetype='application/json', as_attachment=True, download_name=f"facturas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
