# Project Social MEdi4

## 🌐 Descripción General

Project Social MEdi4 es un proyecto desarrollado en **Python** orientado a la gestión de información, análisis y funcionalidades relacionadas con usuarios, metodologías y generación de reportes.  
El sistema está organizado de forma modular, permitiendo una clara separación de responsabilidades entre lógica de negocio, manejo de datos y utilidades de análisis.

Este repositorio contiene el código base, scripts de procesamiento, conexión a base de datos y herramientas para expandir funcionalidades.

---

## 📁 Estructura del Proyecto
/
├── .vscode/ # Configuración opcional para VS Code
├── templates/ # Carpeta para plantillas (HTML, textos, etc.)
├── db.py # Manejo y conexión a base de datos
├── models.py # Modelos de datos y estructuras principales
├── user.py # Lógica referente a usuarios
├── methodology.py # Procesos/metodologías de negocio
├── benefit.py # Módulo relacionado con beneficios / cálculos
├── analysis.py # Scripts de análisis
├── reports.py # Generación de reportes
├── main.py # Punto principal de ejecución
├── requirements.txt # Dependencias del proyecto
└── README.md # Documentación principal

**Nota:** Directorios como `myvenv/` o `__pycache__/` deben excluirse usando `.gitignore`.

---

## 📦 Tecnologías Utilizadas

El proyecto está desarrollado sobre Python 3.8+ y 
utiliza un conjunto sólido de tecnologías principales que 
estructuran el funcionamiento completo del sistema. La base del backend se sostiene 
en FastAPI como framework web y Uvicorn como servidor ASGI, mientras que la capa de 
datos se gestiona mediante SQLModel y SQLAlchemy, que combinan tipado moderno con 
un ORM potente y flexible. Para la validación de datos y esquemas se emplea Pydantic, 
y la comunicación asíncrona y manejo de redes se apoyan en librerías como httpx, anyio 
y websockets. El proyecto también integra el ecosistema de Supabase (auth, storage, realtime 
y postgrest) para autenticación, persistencia remota y sincronización en tiempo real. Además, 
utiliza Jinja2 para plantillas, ReportLab para generación de documentos PDF, y python-dotenv para 
la gestión de variables de entorno. Con este conjunto de herramientas principales, el proyecto 
cuenta con una arquitectura robusta, escalable y bien estructurada.

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
class Methodology(MethodologyBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    users: List["User"] = Relationship(
        back_populates="methodologies",
        link_model=UserMethodologyLink
    )
    benefits: List["Benefit"] = Relationship(
        back_populates="methodologies",
        link_model=MethodologyBenefitLink
    )

    Este modelo representa una metodología dentro del sistema y muestra claramente:

Su relación N:M con User, enlazada mediante UserMethodologyLink.
Su relación N:M con Benefit, enlazada mediante MethodologyBenefitLink.


## 📊 Tabla de Relaciones del Modelo de Datos
Modelo A	Relación	Modelo B	Tipo / Detalle
User	N:M	Methodology	Relación mediante la tabla intermedia UserMethodologyLink. Cada usuario puede tener varias metodologías y cada metodología puede pertenecer a varios usuarios.
Methodology	N:M	Benefit	Relación a través de la tabla MethodologyBenefitLink. Una metodología puede tener múltiples beneficios y un beneficio puede estar asociado a varias metodologías.
User	1:N	Analysis	Un usuario puede tener muchos análisis; cada análisis pertenece a un único usuario.
User	1:N	UserAudit	Un usuario puede tener múltiples registros de auditoría. Cada auditoría pertenece a un solo usuario.
Methodology	↔ Intermedia	UserMethodologyLink	Tabla puente que almacena pares (user_id – methodology_id).
Methodology	↔ Intermedia	MethodologyBenefitLink	Tabla puente que relaciona metodologías con beneficios.



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
git clone https://github.com/Iv4n-0v/Project_Social_MEdi4.git
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
