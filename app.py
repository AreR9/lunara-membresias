import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash
from db import get_connection
import re
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
@app.route('/base')
def base():
    return render_template('base.html')
@app.route('/')
def home():
    return render_template('base.html')

# crud staff -------------------------------------------------------------------------b
# Leer
@app.route('/staff', methods=['GET'])
def staff_form():
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)  # <- clave: regresa diccionarios, no tuplas
    cursor.execute("""
        SELECT id, name AS nombre, lastname AS apellido,
               username AS usuario, email AS correo
        FROM user
    """)
    lista_staff = cursor.fetchall()
    cursor.close()
    conexion.close()
    return render_template('staff_form.html', lista_staff=lista_staff, staff_editar=None)

# crear
@app.route('/staff/guardar', methods=['POST'])
def staff_guardar():
    nombre = request.form.get('nombre', '')
    apellido = request.form.get('apellido', '')
    usuario = request.form.get('usuario', '')
    correo = request.form.get('correo', '')
    password = request.form.get('password', '')

    #  Validar que no haya campos vacíos
    if not all([nombre.strip(), apellido.strip(), usuario.strip(), correo.strip(), password.strip()]):
        flash("Todos los campos son obligatorios", "error")
        return redirect(url_for('staff_form'))

    # Abrimos la conexión
    conexion = get_connection()
    cursor = conexion.cursor()

    # Consultar si el username o correo ya existen en la base de datos
    cursor.execute(
        "SELECT id FROM user WHERE username = %s OR email = %s",
        (usuario, correo)
    )
    usuario_existente = cursor.fetchone()

    # Si encontramos una coincidencia, detenemos el registro
    if usuario_existente:
        cursor.close()
        conexion.close()
        flash("El nombre de usuario o correo ya esta en uso", "error")
        return redirect(url_for('staff_form'))

    #Si no existe duplicado, insertamos al nuevo empleado
    cursor.execute(
        "INSERT INTO user (name, lastname, username, email, password) VALUES (%s, %s, %s, %s, %s)",
        (nombre, apellido, usuario, correo, password)
    )
    conexion.commit()
    cursor.close()
    conexion.close()

    flash("Empleado registrado correctamente", "success")
    return redirect(url_for('staff_form'))

# editar
@app.route('/staff/editar/<int:id>', methods=['GET'])
def staff_editar(id):
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # hace select del user a editar y lo guarda en persona
        cursor.execute("""
            SELECT id, name AS nombre, lastname AS apellido,
                   username AS usuario, email AS correo
            FROM user WHERE id = %s
        """, (id,))
        persona = cursor.fetchone()

        # Si el usuario no existe en la BD
        if not persona:
            flash("El empleado que intentas editar no existe.", "error")
            return redirect(url_for('staff_form'))

        #  Cargar la lista completa de empleados para la tabla
        cursor.execute("""
            SELECT id, name AS nombre, lastname AS apellido,
                   username AS usuario, email AS correo
            FROM user
        """)
        lista_staff = cursor.fetchall()

        return render_template('staff_form.html', lista_staff=lista_staff, staff_editar=persona)

    except Exception as e:
        flash("Ocurrio un error al recuperar la informacion del empleado.", "error")
        return redirect(url_for('staff_form'))

    finally:
        cursor.close()
        conexion.close()


# actualizar
@app.route('/staff/actualizar/<int:id>', methods=['POST'])
def staff_actualizar(id):
    nombre = request.form.get('nombre', '').strip()#el request rescata lo que hay escrito en el formulario
    apellido = request.form.get('apellido', '').strip()
    usuario = request.form.get('usuario', '').strip()
    correo = request.form.get('correo', '').strip()

    # rechazar campos vacios
    if not all([nombre, apellido, usuario, correo]):
        flash("Todos los campos (Nombre, Apellido, Usuario, Correo) son obligatorios.", "error")
        return redirect(url_for('staff_editar', id=id))

    # validacion dde correo regex
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, correo):
        flash("El formato del correo electronico no es valido.", "error")
        return redirect(url_for('staff_editar', id=id))

    conexion = get_connection()
    cursor = conexion.cursor()

    try:
        # buscamos si hay ya un nombre de usuario igual
        cursor.execute("SELECT id FROM user WHERE username = %s AND id != %s", (usuario, id))
        if cursor.fetchone():
            #en dado caso que si manda un mensaje flash
            flash(f"El nombre de usuario '{usuario}' ya esta en uso por otro empleado.", "error")
            return redirect(url_for('staff_editar', id=id))

        # ahira seguimos con el correo si hay un correo igual manda mensaje flash
        cursor.execute("SELECT id FROM user WHERE email = %s AND id != %s", (correo, id))
        if cursor.fetchone():
            flash(f"El correo electronico '{correo}' ya esta en uso por otro empleado.", "error")
            return redirect(url_for('staff_editar', id=id))

        # los actualiza
        cursor.execute("""
            UPDATE user 
            SET name = %s, lastname = %s, username = %s, email = %s
            WHERE id = %s
        """, (nombre, apellido, usuario, correo, id))
        
        conexion.commit()#mensaje
        flash("Datos del empleado actualizados correctamente.", "success")
        return redirect(url_for('staff_form'))

    except Exception as e:
        conexion.rollback()#mensaje
        flash("Ocurrio un problema en la base de datos al intentar actualizar.", "error")
        return redirect(url_for('staff_editar', id=id))

    finally:
        cursor.close()
        conexion.close()

@app.route('/staff/eliminar/<int:id>', methods=['GET'])
def staff_eliminar(id):
    conexion = get_connection()
    cursor = conexion.cursor()

    try:
        # 1. Quitar la referencia en pagos (pone NULL al operador que hizo el pago)
        cursor.execute("UPDATE payment SET user_id = NULL WHERE user_id = %s", (id,))
        
        # 2. Borrar físicamente el usuario de la BD
        cursor.execute("DELETE FROM user WHERE id = %s", (id,))
        
        conexion.commit()
        flash("Empleado eliminado permanentemente de la base de datos.", "success")

    except Exception as e:
        conexion.rollback()
        print(f"--- ERROR AL BORRAR STAFF: {e} ---")
        flash(f"Error al eliminar de la base de datos: {e}", "error")

    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for('staff_form'))


# crud clientes----------------------------
@app.route('/clientes', methods=['GET'])
def clientes_form():
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT id, 
                   name AS nombre, 
                   lastname AS apellido, 
                   email AS correo, 
                   phone AS telefono, 
                   identity_card AS documento 
            FROM client
        """)
        lista_clientes = cursor.fetchall()
        return render_template('clientes_form.html', lista_clientes=lista_clientes, cliente_editar=None)
    
    except Exception as e:
      
        print(f"--- ERROR MYSQL AL CARGAR CLIENTES: {e} ---")
        flash(f"Error al cargar clientes: {e}", "error")
        return render_template('clientes_form.html', lista_clientes=[], cliente_editar=None)
        
    finally:
        cursor.close()
        conexion.close()


@app.route('/clientes/guardar', methods=['POST'])
def clientes_guardar():
    nombre = request.form.get('nombre', '').strip()
    apellido = request.form.get('apellido', '').strip()
    documento = request.form.get('documento', '').strip()
    correo = request.form.get('correo', '').strip()
    telefono = request.form.get('telefono', '').strip()

    # campos vacios
    if not all([nombre, apellido, documento, correo, telefono]):
        flash("Todos los campos son obligatorios.", "error")
        return redirect(url_for('clientes_form'))

    # correo
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, correo):
        flash("El formato del correo electronico no es valido.", "error")
        return redirect(url_for('clientes_form'))

    conexion = get_connection()
    cursor = conexion.cursor()

    try:
        # Validar duplicado de correo
        cursor.execute("SELECT id FROM client WHERE email = %s", (correo,))
        if cursor.fetchone():
            flash(f"El correo '{correo}' ya esta registrado con otro cliente.", "error")
            return redirect(url_for('clientes_form'))

        # revisar duplicado de documento (Identity Card)
        cursor.execute("SELECT id FROM client WHERE identity_card = %s", (documento,))
        if cursor.fetchone():
            flash(f"El documento '{documento}' ya esta registrado con otro cliente.", "error")
            return redirect(url_for('clientes_form'))

        # Insertar nuevo cliente 
        cursor.execute(
            """
            INSERT INTO client (name, lastname, identity_card, email, phone) 
            VALUES (%s, %s, %s, %s, %s)
            """,
            (nombre, apellido, documento, correo, telefono)
        )
        conexion.commit()
        flash("Cliente registrado correctamente.", "success")

    except Exception as e:
        conexion.rollback()
        print(f"Error detallado de MySQL: {e}")
        flash(f"Error al registrar el cliente: {e}", "error")

    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for('clientes_form'))

@app.route('/clientes/editar/<int:id>', methods=['GET'])
def clientes_editar(id):
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # hace select del cliente a editar y lo guarda en cliente
        cursor.execute("""
            SELECT id, name AS nombre,lastname AS apellido, email AS correo, phone AS telefono, identity_card AS documento   
            FROM client WHERE id = %s
        """, (id,))
        cliente = cursor.fetchone()

        # Si el cliente no existe en la BD
        if not cliente:
            flash("El cliente que intentas editar no existe.", "error")
            return redirect(url_for('clientes_form'))
# Cargar la lista completa de clientes para la tabla
        cursor.execute("""
            SELECT id, name AS nombre,lastname AS apellido, email AS correo, phone AS telefono, identity_card AS documento
            FROM client
        """)
        lista_clientes = cursor.fetchall()

        return render_template('clientes_form.html', lista_clientes=lista_clientes, cliente_editar=cliente)

    except Exception as e:
        flash("Ocurrio un error al recuperar la informacion del cliente.", "error")
        return redirect(url_for('clientes_form'))

    finally:
        cursor.close()
        conexion.close()

@app.route('/clientes/actualizar/<int:id>', methods=['POST'])
def clientes_actualizar(id):
    nombre = request.form.get('nombre', '').strip()
    apellido = request.form.get('apellido', '').strip()
    documento = request.form.get('documento', '').strip()
    correo = request.form.get('correo', '').strip()
    telefono = request.form.get('telefono', '').strip()

    # Validar campos vacíos
    if not all([nombre, apellido, documento, correo, telefono]):
        flash("Todos los campos son obligatorios.", "error")
        return redirect(url_for('clientes_editar', id=id))

    # Validar formato de correo
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, correo):
        flash("El formato del correo electronico no es valido.", "error")
        return redirect(url_for('clientes_editar', id=id))

    conexion = get_connection()
    cursor = conexion.cursor()

    try:
        cursor.execute("SELECT id FROM client WHERE email = %s AND id != %s", (correo, id))
        if cursor.fetchone():
            flash(f"El correo '{correo}' ya esta en uso por otro cliente.", "error")
            return redirect(url_for('clientes_editar', id=id))
        cursor.execute("SELECT id FROM client WHERE identity_card = %s AND id != %s", (documento, id))
        if cursor.fetchone():
            flash(f"El documento '{documento}' ya esta en uso por otro cliente.", "error")
            return redirect(url_for('clientes_editar', id=id))
        
        # Actualizar cliente
        cursor.execute("""
            UPDATE client 
            SET name = %s,lastname = %s, email = %s, phone = %s, identity_card = %s
            WHERE id = %s
        """, (nombre, apellido, correo, telefono, documento, id))
        
        conexion.commit()
        flash("Datos del cliente actualizados correctamente.", "success")
        return redirect(url_for('clientes_form'))

    except Exception as e:
        conexion.rollback()
        flash("Ocurrio un problema en la base de datos al intentar actualizar.", "error")
        return redirect(url_for('clientes_editar', id=id))

    finally:
        cursor.close()
        conexion.close()

@app.route('/clientes/eliminar/<int:id>', methods=['GET'])
def clientes_eliminar(id):
    conexion = get_connection()
    cursor = conexion.cursor()

    try:
        # 1. Borrar primero los pagos vinculados a las suscripciones de este cliente
        cursor.execute("""
            DELETE p FROM payment p 
            INNER JOIN contract c ON p.contract_id = c.id 
            WHERE c.client_id = %s
        """, (id,))
        
        # 2. Borrar las suscripciones/contratos del cliente
        cursor.execute("DELETE FROM contract WHERE client_id = %s", (id,))
        
        # borrar defiinitivamente al cliente de la BD
        cursor.execute("DELETE FROM client WHERE id = %s", (id,))
        
        conexion.commit()
        flash("Cliente y su historial eliminados permanentemente.", "success")

    except Exception as e:
        conexion.rollback()
        print(f"--- ERROR AL BORRAR CLIENTE: {e} ---")
        flash(f"Error al eliminar de la base de datos: {e}", "error")

    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for('clientes_form'))

#crud planes----------------------------
@app.route('/planes', methods=['GET'])  
def planes_form():
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT id, name AS nombre, description AS descripcion, price AS precio, duration_days AS duracion
            FROM membership
        """)
        lista_planes = cursor.fetchall()
        return render_template('planes_form.html', lista_planes=lista_planes, plan_editar=None)
    
    except Exception as e:
        print(f"--- ERROR MYSQL AL CARGAR PLANES: {e} ---")
        flash(f"Error al cargar planes: {e}", "error")
        return render_template('planes_form.html', lista_planes=[], plan_editar=None)
        
    finally:
        cursor.close()
        conexion.close()

@app.route('/planes/guardar', methods=['POST'])
def planes_guardar():
    nombre = request.form.get('nombre', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    precio = request.form.get('precio', '').strip()
    duracion = request.form.get('duracion', '').strip()

    # Validar campos vacíos
    if not all([nombre, descripcion, precio, duracion]):
        flash("Todos los campos son obligatorios.", "error")
        return redirect(url_for('planes_form'))

    # Validar precio y duración
    try:
        precio_val = float(precio)
        duracion_val = int(duracion)
        if precio_val <= 0 or duracion_val <= 0:
            raise ValueError
    except ValueError:
        flash("El precio y la duracion deben ser valores numericos mayores a cero.", "error")
        return redirect(url_for('planes_form'))

    conexion = get_connection()
    cursor = conexion.cursor()

    try:
        # Insertar nuevo plan
        cursor.execute(
            """
            INSERT INTO membership (name, description, price, duration_days) 
            VALUES (%s, %s, %s, %s)
            """,
            (nombre, descripcion, precio_val, duracion_val)
        )
        conexion.commit()
        flash("Plan registrado correctamente.", "success")

    except Exception as e:
        conexion.rollback()
        print(f"Error detallado de MySQL: {e}")
        flash(f"Error al registrar el plan: {e}", "error")

    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for('planes_form'))

@app.route('/planes/editar/<int:id>', methods=['GET'])
def planes_editar(id):
   
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)
    
    try:
        # hace select del plan a editar y lo guarda en plan
        cursor.execute("""
            SELECT id, name AS nombre, description AS descripcion, price AS precio, duration_days AS duracion   
            FROM membership WHERE id = %s
        """, (id,))
        plan = cursor.fetchone()

        # Si el plan no existe en la BD
        if not plan:
            flash("El plan que intentas editar no existe.", "error")
            return redirect(url_for('planes_form'))

        # Cargar la lista completa de planes para la tabla
        cursor.execute("""
            SELECT id, name AS nombre, description AS descripcion, price AS precio, duration_days AS duracion
            FROM membership
        """)
        lista_planes = cursor.fetchall()

        return render_template('planes_form.html', lista_planes=lista_planes, plan_editar=plan)

    except Exception as e:
        flash("Ocurrio un error al recuperar la informacion del plan.", "error")
        return redirect(url_for('planes_form'))

    finally:
        cursor.close()
        conexion.close()

@app.route('/planes/actualizar/<int:id>', methods=['POST'])
def planes_actualizar(id):
    nombre = request.form.get('nombre', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    precio = request.form.get('precio', '').strip()
    duracion = request.form.get('duracion', '').strip()

    # Validar campos vacíos
    if not all([nombre, descripcion, precio, duracion]):
        flash("Todos los campos son obligatorios.", "error")
        return redirect(url_for('planes_editar', id=id))

    # Validar precio y duración
    try:
        precio_val = float(precio)
        duracion_val = int(duracion)
        if precio_val <= 0 or duracion_val <= 0:
            raise ValueError
    except ValueError:
        flash("El precio y la duracion deben ser valores numericos mayores a cero.", "error")
        return redirect(url_for('planes_editar', id=id))

    conexion = get_connection()
    cursor = conexion.cursor()

    try:
        # Actualizar plan
        cursor.execute("""
            UPDATE membership 
            SET name = %s, description = %s, price = %s, duration_days = %s
            WHERE id = %s
        """, (nombre, descripcion, precio_val, duracion_val, id))
        
        conexion.commit()
        flash("Datos del plan actualizados correctamente.", "success")

    except Exception as e:
        conexion.rollback()
        flash("Ocurrio un problema en la base de datos al intentar actualizar.", "error")
        return redirect(url_for('planes_editar', id=id))

    finally:
        cursor.close()
        conexion.close()
    return redirect(url_for('planes_form'))


@app.route('/planes/eliminar/<int:id>', methods=['GET'])
def planes_eliminar(id):
    conexion = get_connection()
    cursor = conexion.cursor()

    try:
        # 1. Borrar los pagos vinculados a contratos con este plan
        cursor.execute("""
            DELETE p FROM payment p 
            INNER JOIN contract c ON p.contract_id = c.id 
            WHERE c.membership_id = %s
        """, (id,))
        
        # 2. Borrar las suscripciones asociadas a este plan
        cursor.execute("DELETE FROM contract WHERE membership_id = %s", (id,))
        
        # 3. Borrar físicamente el plan de la BD
        cursor.execute("DELETE FROM membership WHERE id = %s", (id,))
        
        conexion.commit()
        flash("Plan eliminado permanentemente de la base de datos.", "success")

    except Exception as e:
        conexion.rollback()
        print(f"--- ERROR AL BORRAR PLAN: {e} ---")
        flash(f"Error al eliminar de la base de datos: {e}", "error")

    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for('planes_form'))
     

#crud suscripciones----------------------------
@app.route('/suscripciones', methods=['GET'])
def suscripciones_form():
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)
    
    try:
        #el select concatena el nombre y apellido para mostrarlo en el combo box
        cursor.execute("""
            SELECT id, CONCAT(name, ' ', lastname) AS nombre_completo, email 
            FROM client 
            WHERE is_active = 1
        """)
        lista_clientes = cursor.fetchall()#lo guarda en una lista de diccionarios para poder usarlo en el combo box

       
        #el select trae los planes activos de la tabla membership para mostrarlos en el combo box
        cursor.execute("""
            SELECT id, name AS nombre, price AS precio, duration_days AS duracion 
            FROM membership 
            WHERE is_active = 1
        """)
        lista_planes = cursor.fetchall()

        # utilizamos un inner join para traer los datos de la tabla contract, client y membership para mostrarlos en la tabla de suscripciones
    #c. de tabla suscripciones cl. tabla de clientes m. tabla de planes
    #obtenemos id de sub despues concatenamos el nombre y apellido 
    #obtenemos el nombre del plan, la fecha de inicio y fin y el estado de la suscripcion

        cursor.execute("""
            SELECT 
                c.id,
                CONCAT(cl.name, ' ', cl.lastname) AS cliente_nombre, 
                m.name AS plan_nombre,
                c.start_date AS fecha_inicio,
                c.end_date AS fecha_fin,
                c.status AS estado
            FROM contract c
            INNER JOIN client cl ON c.client_id = cl.id
            INNER JOIN membership m ON c.membership_id = m.id
            ORDER BY c.id DESC
        """)
        lista_suscripciones = cursor.fetchall()

        return render_template(
            'suscripciones_form.html', 
            lista_clientes=lista_clientes, 
            lista_planes=lista_planes, 
            lista_suscripciones=lista_suscripciones
        )

    except Exception as e:
        print(f"--- ERROR AL CARGAR SUSCRIPCIONES: {e} ---")
        flash(f"Error al cargar el modulo: {e}", "error")
        return render_template('suscripciones_form.html', lista_clientes=[], lista_planes=[], lista_suscripciones=[])
        
    finally:
        cursor.close()
        conexion.close()    


@app.route('/suscripciones/guardar', methods=['POST'])
def suscripciones_guardar():
    # Esta funcion recibe los datos del formulario de suscripcion
    # y valida todo antes de guardarlo en la base de datos.
    # Coincide exactamente con los 'name' de tu HTML:
    cliente_id = request.form.get('cliente_id', '').strip()
    membresia_id = request.form.get('membresia_id', '').strip()
    fecha_inicio_str = request.form.get('fecha_inicio', '').strip()
    estado = request.form.get('estado', '').strip()

    #Validaicon nada vacio
    if not all([cliente_id, membresia_id, fecha_inicio_str, estado]):
        flash("Todos los campos son obligatorios.", "error")
        return redirect(url_for('suscripciones_form'))

    #el estado sio si 1 o 0
    if estado not in ('0', '1'):
        flash("El estado seleccionado no es valido.", "error")
        return redirect(url_for('suscripciones_form'))

    # valida que los id del cliente y plan sea an num enteros
    try:
        cliente_id_int = int(cliente_id)
        membresia_id_int = int(membresia_id)
        if cliente_id_int <= 0 or membresia_id_int <= 0:
            raise ValueError
    except ValueError:
        flash("Cliente y plan deben seleccionarse correctamente.", "error")
        return redirect(url_for('suscripciones_form'))

    # recibimos la fecha y la convierte en datetime para poder calcular despues el fehca final
    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
    except ValueError:
        flash("El formato de fecha ingresado no es valido.", "error")
        return redirect(url_for('suscripciones_form'))

  
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    try:
        # 6. Validar que el cliente exista 
        cursor.execute("SELECT id FROM client WHERE id = %s AND is_active = 1", (cliente_id_int,))
        if not cursor.fetchone():
            flash("El cliente seleccionado no existe o no esta activo.", "error")
            return redirect(url_for('suscripciones_form'))

        #validacion para no permitir que si ya tiene sub haga mas sin parar
        cursor.execute("SELECT id FROM contract WHERE client_id = %s AND status = 1", (cliente_id_int,))
        if cursor.fetchone():
            flash("El cliente ya tiene una suscripcion activa. Debes dar de baja la suscripcion actual antes de crear otra.", "error")
            return redirect(url_for('suscripciones_form'))

        # revisa que el plan si este activo
        cursor.execute("SELECT id, duration_days FROM membership WHERE id = %s AND is_active = 1", (membresia_id_int,))
        plan = cursor.fetchone()

        if not plan or plan['duration_days'] <= 0:
            flash("El plan seleccionado no es valido.", "error")
            return redirect(url_for('suscripciones_form'))

        # Calcular la fecha de fin con la duracio del plan
        end_date = fecha_inicio + timedelta(days=plan['duration_days'])
        if end_date <= fecha_inicio:
            flash("La fecha de fin debe ser posterior a la fecha de inicio.", "error")
            return redirect(url_for('suscripciones_form'))

        #Guardar el contrato en la base de datos
        cursor.execute(
            """
            INSERT INTO contract (client_id, membership_id, start_date, end_date, status, created_at) 
            VALUES (%s, %s, %s, %s, %s, NOW())
            """,
            (cliente_id_int, membresia_id_int, fecha_inicio, end_date, int(estado))
        )
        
        conexion.commit()
        flash("Suscripcion registrada correctamente!", "success")

    except Exception as e:
        conexion.rollback()
        print(f"--- ERROR MYSQL: {e} ---")
        flash(f"Error al registrar la suscripcion: {e}", "error")

    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for('suscripciones_form'))

@app.route('/suscripciones/editar/<int:id>', methods=['GET'])
def suscripciones_editar(id):
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    try:
        #obtener la suscripcion a editar
        cursor.execute("""
            SELECT 
                c.id, 
                c.client_id, 
                c.membership_id, 
                c.start_date, 
                c.end_date, 
                c.status
            FROM contract c
            WHERE c.id = %s
        """, (id,))
        suscripcion = cursor.fetchone()

        if not suscripcion:
            flash("La suscripcion que intentas editar no existe.", "error")
            return redirect(url_for('suscripciones_form'))

        # obtener lista de clientes activos
        cursor.execute("""
            SELECT id, CONCAT(name, ' ', lastname) AS nombre_completo 
            FROM client 
            WHERE is_active = 1
        """)
        lista_clientes = cursor.fetchall()

        #obtener lista de planes activos
        cursor.execute("""
            SELECT id, name AS nombre, price AS precio, duration_days AS duracion 
            FROM membership 
            WHERE is_active = 1
        """)
        lista_planes = cursor.fetchall()

        # ibtener el historial de suscripciones para mostrar en la tabla
        cursor.execute("""
            SELECT 
                c.id,
                CONCAT(cl.name, ' ', cl.lastname) AS cliente_nombre, 
                m.name AS plan_nombre,
                c.start_date AS fecha_inicio,
                c.end_date AS fecha_fin,
                c.status AS estado
            FROM contract c
            INNER JOIN client cl ON c.client_id = cl.id
            INNER JOIN membership m ON c.membership_id = m.id
            ORDER BY c.id DESC
        """)
        lista_suscripciones = cursor.fetchall()

        return render_template(
            'suscripciones_form.html', 
            lista_clientes=lista_clientes, 
            lista_planes=lista_planes, 
            lista_suscripciones=lista_suscripciones,
            suscripcion_editar=suscripcion
        )

    except Exception as e:
        print(f"--- ERROR MYSQL AL EDITAR SUSCRIPCION: {e} ---")
        flash(f"Error al cargar la suscripcion para editar: {e}", "error")
        return redirect(url_for('suscripciones_form'))

    finally:
        cursor.close()
        conexion.close()    


@app.route('/suscripciones/actualizar/<int:id>', methods=['POST'])
def suscripciones_actualizar(id):
    cliente_id = request.form.get('cliente_id', '').strip()
    membresia_id = request.form.get('membresia_id', '').strip()
    fecha_inicio_str = request.form.get('fecha_inicio', '').strip()
    estado = request.form.get('estado', '').strip()

    # Validacione de campos vaicos
    if not all([cliente_id, membresia_id, fecha_inicio_str, estado]):
        flash("Todos los campos son obligatorios.", "error")
        return redirect(url_for('suscripciones_editar', id=id))

    if estado not in ('0', '1'):
        flash("El estado seleccionado no es valido.", "error")
        return redirect(url_for('suscripciones_editar', id=id))

    try:
        cliente_id_int = int(cliente_id)
        membresia_id_int = int(membresia_id)
        if cliente_id_int <= 0 or membresia_id_int <= 0:
            raise ValueError
    except ValueError:
        flash("Cliente y plan deben seleccionarse correctamente.", "error")
        return redirect(url_for('suscripciones_editar', id=id))

    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
    except ValueError:
        flash("El formato de fecha ingresado no es valido.", "error")
        return redirect(url_for('suscripciones_editar', id=id))

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    try:
        # Validar existencia del cliente activo
        cursor.execute("SELECT id FROM client WHERE id = %s AND is_active = 1", (cliente_id_int,))
        if not cursor.fetchone():
            flash("El cliente seleccionado no existe o no esta activo.", "error")
            return redirect(url_for('suscripciones_editar', id=id))

        # Validar que el plan exista y este activo
        cursor.execute("SELECT id, duration_days FROM membership WHERE id = %s AND is_active = 1", (membresia_id_int,))
        plan = cursor.fetchone()
        if not plan or plan['duration_days'] <= 0:
            flash("El plan seleccionado no es valido.", "error")
            return redirect(url_for('suscripciones_editar', id=id))

        # Calcular la fecha de fin a partir de la duración del plan
        end_date = fecha_inicio + timedelta(days=plan['duration_days'])
        if end_date <= fecha_inicio:
            flash("La fecha de fin debe ser posterior a la fecha de inicio.", "error")
            return redirect(url_for('suscripciones_editar', id=id))

        # Actualizar la suscripción en la base de datos
        cursor.execute(
            """
            UPDATE contract
            SET client_id = %s,
                membership_id = %s,
                start_date = %s,
                end_date = %s,
                status = %s
            WHERE id = %s
            """,
            (cliente_id_int, membresia_id_int, fecha_inicio, end_date, int(estado), id)
        )
        conexion.commit()
        flash("Suscripcion actualizada correctamente.", "success")
        return redirect(url_for('suscripciones_form'))

    except Exception as e:
        conexion.rollback()
        print(f"--- ERROR MYSQL AL ACTUALIZAR SUSCRIPCION: {e} ---")
        flash("No se pudo actualizar la suscripcion. Intenta de nuevo.", "error")
        return redirect(url_for('suscripciones_editar', id=id))

    finally:
        cursor.close()
        conexion.close()
        
@app.route('/suscripciones/baja/<int:id>', methods=['GET'])
def suscripciones_baja(id):
    # Esta ruta se usa cuando el usuario hace clic en "DAR DE BAJA"
    # en la lista de contratos.
    conexion = get_connection()
    cursor = conexion.cursor()

    try:
        # Revisar si la suscripcion existe
        cursor.execute("SELECT status FROM contract WHERE id = %s", (id,))
        suscripcion = cursor.fetchone()
        if not suscripcion:
            flash("La suscripcion que intentas dar de baja no existe.", "error")
            return redirect(url_for('suscripciones_form'))

        # Si ya está inactiva, no hacemos nada
        if suscripcion[0] == 0:
            flash("La suscripcion ya esta inactiva.", "info")
            return redirect(url_for('suscripciones_form'))

        # Cambiar el estado de la suscripción a inactivo
        cursor.execute("UPDATE contract SET status = 0 WHERE id = %s", (id,))
        conexion.commit()
        flash("Suscripcion dada de baja correctamente.", "success")

    except Exception as e:
        conexion.rollback()
        flash("No se pudo desactivar la suscripcion debido a un error del servidor.", "error")

    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for('suscripciones_form'))

@app.route('/suscripciones/eliminar/<int:id>', methods=['GET'])
def suscripciones_eliminar(id):
    conexion = get_connection()
    cursor = conexion.cursor()

    try:
        # revisa si la suscripción existe
        cursor.execute("SELECT id FROM contract WHERE id = %s", (id,))
        if not cursor.fetchone():
            flash("La suscripcion que intentas eliminar no existe.", "error")
            return redirect(url_for('suscripciones_form'))

        #si lo encuentra lo borra
        cursor.execute("DELETE FROM contract WHERE id = %s", (id,))
        conexion.commit()
        flash("Suscripcion eliminada con exito.", "success")

    except Exception as e:
        conexion.rollback()
        flash("No se pudo eliminar la suscripcion debido a un error del servidor.", "error")

    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for('suscripciones_form'))

#crud pagos----------------------------
@app.route('/pagos', methods=['GET'])
def pagos_form():
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)
    
    try:
        #creamos un inner join para traer los datos de la tabla contract
        #  client y membership para mostrarlos en el combo box de contratos
        cursor.execute("""
            SELECT 
                c.id, 
                CONCAT(cl.name, ' ', cl.lastname) AS cliente_nombre, 
                m.name AS plan_nombre,
                m.price AS plan_precio
            FROM contract c
            INNER JOIN client cl ON c.client_id = cl.id
            INNER JOIN membership m ON c.membership_id = m.id
            WHERE c.status = 1
            ORDER BY c.id DESC
        """)
        lista_contratos = cursor.fetchall()

        # pedimos la lista de operadores para el combo box de usuarios
        cursor.execute("""
            SELECT id, CONCAT(name, ' ', lastname) AS nombre_completo, username AS usuario 
            FROM user
            ORDER BY name ASC
        """)
        lista_usuarios = cursor.fetchall()

        # 3. Consulta de Historial de Pagos con INNER JOIN
        cursor.execute("""
            SELECT 
                p.id,
                p.contract_id,
                CONCAT(cl.name, ' ', cl.lastname) AS cliente_nombre,
                p.amount AS monto,
                p.payment_method AS metodo_pago,
                CONCAT(u.name, ' ', u.lastname) AS operador_nombre,
                p.payment_date AS fecha
            FROM payment p
            INNER JOIN contract c ON p.contract_id = c.id
            INNER JOIN client cl ON c.client_id = cl.id
            INNER JOIN user u ON p.user_id = u.id
            ORDER BY p.id DESC
        """)
        lista_pagos = cursor.fetchall()

        return render_template(
            'pagos_form.html', 
            lista_contratos=lista_contratos, 
            lista_usuarios=lista_usuarios, 
            lista_pagos=lista_pagos,
            pago_editar=None
        )

    except Exception as e:
        print(f"--- ERROR AL CARGAR PAGOS: {e} ---")
        flash(f"Error al cargar modulo de pagos: {e}", "error")
        return render_template('pagos_form.html', lista_contratos=[], lista_usuarios=[], lista_pagos=[], pago_editar=None)
        
    finally:
        cursor.close()
        conexion.close()


@app.route('/pagos/guardar', methods=['POST'])
def pagos_guardar():
    contrato_id = request.form.get('contrato_id', '').strip()
    usuario_id = request.form.get('usuario_id', '').strip()
    monto_str = request.form.get('monto', '').strip()
    metodo_pago = request.form.get('metodo_pago', '').strip()

    
    if not all([contrato_id, usuario_id, monto_str, metodo_pago]):
        flash("Todos los campos del pago son obligatorios.", "error")
        return redirect(url_for('pagos_form'))

    try:
        monto = float(monto_str)
        if monto <= 0:
            flash("El monto del pago debe ser un valor superior a cero.", "error")
            return redirect(url_for('pagos_form'))
    except ValueError:
        flash("El monto introducido debe ser un valor numerico valido.", "error")
        return redirect(url_for('pagos_form'))

  
    try:
        contrato_id_int = int(contrato_id)
        usuario_id_int = int(usuario_id)
    except ValueError:
        flash("Seleccion de contrato u operador no valida.", "error")
        return redirect(url_for('pagos_form'))

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    try:
     #buscamos si el contrato y el usuario existen antes de insertar el pago
        cursor.execute("SELECT id FROM contract WHERE id = %s", (contrato_id_int,))
        if not cursor.fetchone():
            flash("El contrato seleccionado no existe.", "error")
            return redirect(url_for('pagos_form'))

        cursor.execute("SELECT id FROM user WHERE id = %s", (usuario_id_int,))
        if not cursor.fetchone():
            flash("El usuario operador seleccionado no existe.", "error")
            return redirect(url_for('pagos_form'))
        # Validar si el contrato ya tiene un pago registrado
        cursor.execute("SELECT id FROM payment WHERE contract_id = %s", (contrato_id_int,))
        if cursor.fetchone():
            flash("Este contrato ya cuenta con un pago registrado.", "error")
            return redirect(url_for('pagos_form'))

        # metemos registro
        cursor.execute(
            """
            INSERT INTO payment (contract_id, user_id, amount, payment_method, payment_date)
            VALUES (%s, %s, %s, %s, NOW())
            """,
            (contrato_id_int, usuario_id_int, monto, metodo_pago)
        )
        conexion.commit()
        flash("Pago registrado con exito!", "success")

    except Exception as e:
        conexion.rollback()
        print(f"--- ERROR MYSQL PAGOS: {e} ---")
        flash("Ocurrio un error en la base de datos al guardar el pago.", "error")

    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for('pagos_form'))


@app.route('/pagos/editar/<int:id>', methods=['GET'])
def pagos_editar(id):
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id, contract_id, user_id, amount, payment_method FROM payment WHERE id = %s", (id,))
        pago = cursor.fetchone()

        if not pago:
            flash("El pago a editar no existe.", "error")
            return redirect(url_for('pagos_form'))

        # Cargar lista de contratos con precio
        cursor.execute("""
            SELECT 
                c.id, 
                CONCAT(cl.name, ' ', cl.lastname) AS cliente_nombre, 
                m.name AS plan_nombre,
                m.price AS plan_precio
            FROM contract c
            INNER JOIN client cl ON c.client_id = cl.id
            INNER JOIN membership m ON c.membership_id = m.id
            ORDER BY c.id DESC
        """)
        lista_contratos = cursor.fetchall()

        # Cargar lista de operadores
        cursor.execute("SELECT id, CONCAT(name, ' ', lastname) AS nombre_completo, username AS usuario FROM user ORDER BY name ASC")
        lista_usuarios = cursor.fetchall()

        # Cargar historial para mantener visible la tabla mientras se edita
        cursor.execute("""
            SELECT 
                p.id,
                p.contract_id,
                CONCAT(cl.name, ' ', cl.lastname) AS cliente_nombre,
                p.amount AS monto,
                p.payment_method AS metodo_pago,
                CONCAT(u.name, ' ', u.lastname) AS operador_nombre,
                p.payment_date AS fecha
            FROM payment p
            INNER JOIN contract c ON p.contract_id = c.id
            INNER JOIN client cl ON c.client_id = cl.id
            INNER JOIN user u ON p.user_id = u.id
            ORDER BY p.id DESC
        """)
        lista_pagos = cursor.fetchall()

        return render_template(
            'pagos_form.html',
            lista_contratos=lista_contratos,
            lista_usuarios=lista_usuarios,
            lista_pagos=lista_pagos,
            pago_editar=pago
        )

    except Exception as e:
        print(f"--- ERROR AL EDITAR PAGO: {e} ---")
        flash("Error al obtener la informacion del pago.", "error")
        return redirect(url_for('pagos_form'))

    finally:
        cursor.close()
        conexion.close()


@app.route('/pagos/actualizar/<int:id>', methods=['POST'])
def pagos_actualizar(id):
    contrato_id = request.form.get('contrato_id', '').strip()
    usuario_id = request.form.get('usuario_id', '').strip()
    monto_str = request.form.get('monto', '').strip()
    metodo_pago = request.form.get('metodo_pago', '').strip()

    if not all([contrato_id, usuario_id, monto_str, metodo_pago]):
        flash("Todos los campos del pago son obligatorios.", "error")
        return redirect(url_for('pagos_editar', id=id))

    try:
        monto = float(monto_str)
        if monto <= 0:
            flash("El monto del pago debe ser mayor a cero.", "error")
            return redirect(url_for('pagos_editar', id=id))
    except ValueError:
        flash("Monto no valido.", "error")
        return redirect(url_for('pagos_editar', id=id))

    conexion = get_connection()
    cursor = conexion.cursor()

    try:
        cursor.execute(
            """
            UPDATE payment
            SET contract_id = %s, user_id = %s, amount = %s, payment_method = %s
            WHERE id = %s
            """,
            (int(contrato_id), int(usuario_id), monto, metodo_pago, id)
        )
        conexion.commit()
        flash("Pago actualizado correctamente.", "success")
        return redirect(url_for('pagos_form'))

    except Exception as e:
        conexion.rollback()
        print(f"--- ERROR MYSQL ACTUALIZAR PAGO: {e} ---")
        flash("Ocurrio un error al actualizar el registro de pago.", "error")
        return redirect(url_for('pagos_editar', id=id))

    finally:
        cursor.close()
        conexion.close()


@app.route('/pagos/eliminar/<int:id>', methods=['GET'])
def pagos_eliminar(id):
    conexion = get_connection()
    cursor = conexion.cursor()
    # revisa si el pago existe
    #si si lo encuentra lo borra
    cursor.execute("SELECT id FROM payment WHERE id = %s", (id,))
    if not cursor.fetchone():
        flash("El registro de pago que intentas eliminar no existe.", "error")
        return redirect(url_for('pagos_form'))
    try:
        cursor.execute("DELETE FROM payment WHERE id = %s", (id,))
        conexion.commit()
        flash("Registro de pago eliminado con exito.", "success")
    except Exception as e:
        conexion.rollback()
        print(f"--- ERROR ELIMINAR PAGO: {e} ---")
        flash("No se pudo eliminar el registro de pago.", "error")
    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for('pagos_form'))
#reportes

@app.route('/reporte', methods=['GET'])
def reporte_auditoria_ingresos():
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    try:
        # Consulta SQL con JOINs uniendo: contract, client, membership, payment y user
        #m. es membership, c. contract, cl. client, p. payment, u. user
        #coalesce para que si no hay pago o usuario muestre 0.00 o Sin registro / N/A

        query = """
            SELECT 
                CONCAT(cl.name, ' ', cl.lastname) AS cliente_nombre,
                m.name AS plan_nombre,
                c.start_date AS fecha_inicio,
                c.end_date AS fecha_vencimiento,
                CASE 
                    WHEN c.status = 1 THEN 'Activo'
                    ELSE 'Inactivo'
                END AS estado_contrato,
                COALESCE(p.amount, 0.00) AS monto_pago,
                COALESCE(CONCAT(u.name, ' ', u.lastname), 'Sin registro / N/A') AS empleado_nombre
            FROM contract c
            INNER JOIN client cl ON c.client_id = cl.id
            INNER JOIN membership m ON c.membership_id = m.id
            LEFT JOIN payment p ON p.contract_id = c.id
            LEFT JOIN user u ON p.user_id = u.id
            WHERE c.status = 1
            ORDER BY c.start_date DESC, p.payment_date DESC
        """
        cursor.execute(query)
        reporte_data = cursor.fetchall()

        # Renderizamos directamente 'reporte.html'
        return render_template('reporte.html', reporte=reporte_data)

    except Exception as e:
        print(f"--- ERROR EN REPORTE DE AUDITORIA: {e} ---")
        flash(f"Error al generar el reporte: {e}", "error")
        return render_template('reporte.html', reporte=[])

    finally:
        cursor.close()
        conexion.close()

if __name__ == "__main__":
    app.run(debug=True)