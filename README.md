# HAR-228 Voice AI & RAG Microservice

Microservicio de nivel empresarial diseñado para transformar texto en voz en tiempo real, potenciado con **RAG (Retrieval-Augmented Generation)** para respuestas basadas en conocimiento específico de empresas y **Gestión de Sesiones** persistente.

---

## 🚀 Características Avanzadas

- **RAG Multi-tenant**: Búsqueda semántica en base de datos vectorial (**Qdrant**) con aislamiento estricto por `company_id`.
- **Memoria de Sesión**: Persistencia de conversaciones usando **Redis**, permitiendo escalabilidad horizontal.
- **Prompts Dinámicos**: Configuración de "personalidades" y comportamientos por empresa mediante archivos YAML.
- **Inteligencia**: Integración con **OpenRouter** (Mistral, Claude, GPT, etc.) y embeddings con **FastEmbed**.
- **Voz Fluida**: Síntesis de voz natural con **Edge-TTS** alineada al español latino.

---

## 🛠️ Modos de Ejecución

### 1. Ejecución Local (Desarrollo Rápido)

Ideal para probar cambios en el código sin depender de Docker para la aplicación.

1. **Actualizar dependencias**:
   ```powershell
   .\venv\Scripts\python.exe -m pip install -r app/requirements.txt
   ```
2. **Levantar servicios de apoyo (Redis y Qdrant)**:
   ```powershell
   docker-compose up -d redis qdrant
   ```
3. **Inicializar Base Vectorial (Solo la primera vez)**:
   ```powershell
   $env:PYTHONPATH="app"; .\venv\Scripts\python.exe app/scripts/init_qdrant.py
   ```
4. **Iniciar App**:
   ```powershell
   $env:PYTHONPATH="app"; .\venv\Scripts\python.exe -m src.main
   ```

### 2. Ejecución con Docker Compose (Stack Completo)

Levanta todo el ecosistema (App + Redis + Qdrant) en contenedores vinculados.

```powershell
docker-compose up --build
```

---

## 🔗 Acceso Rápido (Local)

Una vez que el servicio esté corriendo, puedes acceder a:
- **Documentación Swagger**: [http://localhost:8000/docs](http://localhost:8000/docs) (Para probar endpoints)
- **Estado del Sistema**: [http://localhost:8000/health](http://localhost:8000/health)
- **Documentación Redoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🏢 Gestión del Conocimiento (Tenant Management)

HAR-228 permite gestionar el conocimiento de múltiples empresas de forma aislada. Soporta:
- **Formatos**: `.txt`, `.pdf` (con OCR), `.xlsx`, `.csv`, `.png`, `.jpg`.
- **OCR Automático**: Si un PDF escaneado o una imagen no tiene texto legible, el sistema intentará extraerlo usando Tesseract.

### 📥 Ingestar un Documento (Vía API)
Puedes usar **Swagger** (`/docs`) o `curl`:
```bash
# Ejemplo subiendo un PDF
curl -X POST "http://localhost:8000/ingest/file" \
     -F "company_id=mi-empresa-pro" \
     -F "file=@/ruta/a/tu/archivo.pdf"
```

### 📁 Ingesta Masiva (Script CLI)
Para cargar carpetas enteras de documentos a una empresa:
```powershell
$env:PYTHONPATH="app"; .\venv\Scripts\python.exe app/scripts/bulk_ingest_folder.py --folder "C:/MisDocumentos/EmpresaA" --company "empresa-a"
```

> **Nota sobre OCR**: Para que el procesamiento de imágenes y PDFs escaneados funcione, debes tener instalado **Tesseract OCR** en tu sistema y disponible en el PATH.

### 🧠 Búsqueda Contextual (Chat)
El sistema buscará automáticamente en la base de datos de la empresa para responder.
```http
GET /chat?text=¿cuanto cuestan los envíos?&company_id=mi-empresa-abc&session_id=usuario-123
```

---

## ☁️ Recomendaciones de Producción

Para un entorno real de alta concurrencia, se recomienda **desacoplar** el almacenamiento de la lógica:

1. **Lógica**: Desplegar el contenedor de HAR-228 en **AWS App Runner** o **Google Cloud Run**.
2. **Vectores**: Usar **Qdrant Cloud** (Servicio gestionado) para evitar administrar infraestructura de bases de datos.
3. **Sesiones**: Usar **Upstash Redis** o **AWS ElastiCache**.
4. **Configuración**: Solo debes cambiar las URLs en el `.env` (ver `.env.example`).

---

## 🏗️ Estructura del Proyecto

```text
├── app/
│   ├── src/
│   │   ├── api/            # Endpoints y Dependencias (Factory)
│   │   ├── application/    # Orquestador RAG y lógica de negocio
│   │   ├── domain/         # Interfaces (Ports) y Entidades
│   │   ├── infrastructure/ # Adaptadores (Redis, Qdrant, OpenRouter, Edge-TTS)
│   │   └── core/           # Configuración y Logging
│   └── scripts/            # Scripts de inicialización
├── tests/                  # Pruebas unitarias con Mocks
├── docker-compose.yml       # Orquestación local de servicios
└── Dockerfile               # Imagen optimizada para producción
```

---

## 🧪 Calidad y Pruebas

```powershell
# Ejecutar tests para validar la orquestación (sin usar créditos)
$env:PYTHONPATH="app"; pytest tests/
```
