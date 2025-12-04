# Project Social MEdi4

## 🌐 Descripción General

Project Social MEdi4 es un proyecto desarrollado en **Python** orientado a la gestión de información,<br>
análisis y funcionalidades relacionadas con usuarios, metodologías y generación de reportes.  <br>
El sistema está organizado de forma modular, permitiendo una clara separación de responsabilidades<br>
entre lógica de negocio, manejo de datos y utilidades de análisis.<br>

---

## 📁 Estructura del Proyecto
/
├── .vscode/ # Configuración opcional para VS Code <br>
├── templates/ # Carpeta para plantillas (HTML, textos, etc.)<br>
├── db.py # Manejo y conexión a base de datos<br>
├── models.py # Modelos de datos y estructuras principales<br>
├── user.py # Lógica referente a usuarios<br>
├── methodology.py # Procesos/metodologías de negocio<br>
├── benefit.py # Módulo relacionado con beneficios / cálculos<br>
├── analysis.py # Scripts de análisis<br>
├── reports.py # Generación de reportes<br>
├── main.py # Punto principal de ejecución<br>
├── requirements.txt # Dependencias del proyecto<br>
└── README.md # Documentación principal<br>

---

## 📦 Tecnologías Utilizadas

FastAPI
Python 3
SQLAlchemy
SQLite
Pydantic
Routers modulares
Jinja2 para interfaz HTML

## Modelo de Base de Datos

El sistema está estructurado mediante un conjunto de modelos relacionados que permiten organizar usuarios, metodologías, beneficios, análisis y auditorías. Las relaciones principales se definen de la siguiente forma:

✔ Relaciones principales

User N:M Methodology
(a través de la tabla intermedia UserMethodologyLink)

Methodology N:M Benefit
(usando la tabla intermedia MethodologyBenefitLink)

User 1:N Analysis
(cada usuario puede tener múltiples análisis registrados)

User 1:N UserAudit
(cada acción de un usuario queda almacenada como auditoría)

---
## Modelo N:M entre User y Metodología
class Methodology(MethodologyBase, table=True):<br>
    id: Optional[int] = Field(default=None, primary_key=True)<br>
    users: List["User"] = Relationship(<br>
        back_populates="methodologies",<br>
        link_model=UserMethodologyLink<br>
    )<br>
    benefits: List["Benefit"] = Relationship(<br>
        back_populates="methodologies",<br>
        link_model=MethodologyBenefitLink<br>
    )<br>

    Este modelo representa una metodología dentro del sistema y muestra claramente:<br>

Su relación N:M con User, enlazada mediante UserMethodologyLink.<br>
Su relación N:M con Benefit, enlazada mediante MethodologyBenefitLink.<br>

## 🚀 Ejecución del Proyecto

Este proyecto está montado en **Render** ;3, por lo que no es necesario instalar nada localmente para probarlo.

### ▶️ **Acceso en Producción**
Solo necesitas ingresar a la siguiente URL:

👉 **https://project-social-medi4.onrender.com**



El backend estará disponible de inmediato, y podrás consumir todos los endpoints sin configuración adicional.

---

## 🛠️ Ejecución Local (Opcional)

Si deseas correr el proyecto localmente:

## 1️⃣ Clonar el repositorio
bash
git clone https://github.com/Iv4n-0v/Project_Social_MEdi4.git<br>
cd Project_Social_MEdi4

## 2️⃣ Crear entorno virtual
python -m venv venv

Activarlo:

Windows

venv\Scripts\activate


Linux/Mac

source venv/bin/activate

## 3️⃣ Instalar dependencias
pip install -r requirements.txt

## 4️⃣ Ejecutar el servidor FastAPI
uvicorn main:app --reload
o
fastapi dev

El proyecto estará disponible en:

👉 http://127.0.0.1:8000

Y la documentación automática de la API:

Swagger UI → /docs

Redoc → /redoc
