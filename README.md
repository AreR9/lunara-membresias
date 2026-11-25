<div align="center">

# 🌙 Lunara

### Sistema web de gestión de membresías para música

**CRUD completo** de clientes, planes, suscripciones, pagos y staff, con reporte consolidado.

<br>

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![CRUD](https://img.shields.io/badge/CRUD-Completo-8B5CF6?style=for-the-badge)

<br>

<img src="capturas/imagen_2026-11-24_215834042.png" alt="Lunara" width="85%">

</div>

---

## ✨ ¿Qué es Lunara?

Una aplicación web para administrar una **plataforma de membresías de música**, con operaciones **CRUD completas** (crear, leer, actualizar y eliminar) en todos sus módulos, y un reporte que cruza toda la información.

## 🎯 Características

| | Módulo | Crear | Leer | Editar | Eliminar |
|:---:|:---|:---:|:---:|:---:|:---:|
| 👤 | **Clientes** | ✅ | ✅ | ✅ | ✅ |
| 🎧 | **Planes** | ✅ | ✅ | ✅ | ✅ |
| 📝 | **Suscripciones** | ✅ | ✅ | ✅ | ✅ |
| 💳 | **Pagos** | ✅ | ✅ | ✅ | ✅ |
| 🧑‍💼 | **Staff** | ✅ | ✅ | ✅ | ✅ |
| 📊 | **Reporte** | | ✅ | | |

Además:

- ✅ Validación de formularios y de usuarios o correos duplicados
- 🔗 Integridad entre tablas: al eliminar un usuario, sus pagos se conservan sin dueño (`user_id = NULL`)
- 🎬 Interfaz con video de fondo
- 🔐 Credenciales y claves fuera del código mediante variables de entorno (`.env`)

## 📸 Captura

<div align="center">

### 🏠 Página de inicio
<img src="capturas/imagen_2026-11-24_215834042.png" alt="Página de inicio de Lunara" width="85%">

</div>

---

## 🛠️ Tecnologías

| Capa | Tecnología |
|:---|:---|
| Backend | Python · Flask |
| Base de datos | MySQL (`mysql-connector-python`) |
| Frontend | HTML · CSS · Jinja2 |
| Configuración | `python-dotenv` |

## 🗄️ Base de datos

El sistema usa la base `sistema_membresias`, con tablas como `user`, `client`, `membership`, `contract` y `payment`.

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/AreR9/lunara-membresias.git
cd lunara-membresias
```

### 2. Crear el entorno virtual e instalar dependencias

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

pip install -r requirements.txt
```

### 3. Crear la base de datos

En MySQL:

```sql
CREATE DATABASE sistema_membresias;
```

Luego importa la estructura:

```bash
mysql -u root -p sistema_membresias < schema.sql
```

### 4. Configurar las variables de entorno

```bash
copy .env.example .env       # Windows
# cp .env.example .env       # Linux / macOS
```

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=tu_contraseña
DB_NAME=sistema_membresias
SECRET_KEY=una_clave_larga_y_aleatoria
```

> 💡 Genera una clave con: `python -c "import secrets; print(secrets.token_hex(32))"`

### 5. Ejecutar

```bash
python app.py
```

Abre **http://localhost:5000** en tu navegador.

## 📁 Estructura

```
lunara-membresias/
├── 📂 static/          → estilos, video y póster de fondo
├── 📂 templates/       → plantillas HTML (Jinja2)
├── 📂 capturas/        → imágenes del README
├── 📄 app.py           → rutas y lógica de la aplicación
├── 📄 db.py            → conexión a MySQL
├── 📄 schema.sql       → estructura de la base de datos
├── 📄 requirements.txt
├── 📄 .env.example     → plantilla de variables de entorno
└── 📄 README.md
```

## 🔮 Próximas mejoras

- [ ] Guardar contraseñas con hash (`werkzeug.security`)
- [ ] Inicio de sesión con roles
- [ ] Exportar el reporte a PDF o Excel
- [ ] Despliegue en la nube

---

<div align="center">

### 👩‍💻 Desarrollado por **Areli Reynoso**

[![GitHub](https://img.shields.io/badge/GitHub-AreR9-181717?style=flat-square&logo=github)](https://github.com/AreR9)

⭐ Si te gustó el proyecto, ¡dale una estrella!

</div>
