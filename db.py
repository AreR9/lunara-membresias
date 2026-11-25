import os
from dotenv import load_dotenv
load_dotenv()

import mysql.connector
 
def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
conexion = get_connection()
cursor = conexion.cursor()

#hago un select basico para ver si funciona la conexion

#Puse un registro de prueba en la tabla de membresias ((1, 'Plan Mensual', 'Acceso basico por 30 dias', Decimal('299.00'), 30, 1))

#pip