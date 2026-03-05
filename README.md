# django-ai-marketplace  
*Django e‑commerce platform powered by LangChain AI product recommendations*

---

## Overview  
`django-ai-marketplace` is a full‑stack e‑commerce solution built on Django that automatically recommends products using LangChain. The system pulls data from a lightweight SQLite database, generates embeddings with an open‑source model (Ollama), and serves real‑time suggestions via the REST API or the web UI.

Why it exists  
- Rapid prototyping of AI‑driven storefronts  
- Demonstrates how to integrate LangChain into a Django project without heavy infrastructure  
- Provides ready‑made tests, Docker support, and CI pipelines for quick onboarding

---

## Features  

* ✅ **Product CRUD** – Create, read, update, delete products through the admin panel or API.  
* 🔍 **AI Recommendations** – On product detail pages, related items are suggested using a hybrid RAG pipeline powered by LangChain.  
* 🛒 **RESTful API** – Endpoints for listing products and fetching recommendations.  
* 📦 **Docker Compose** – Spin up the entire stack (web server + Ollama container) with one command.  
* 🧪 **Test coverage** – Unit tests for models, views, and recommendation logic; CI workflow in GitHub Actions.  
* ⚙️ **Environment‑driven config** – `.env.example` shows required variables; secrets are loaded via `python-decouple`.  

---

## Tech Stack  

| Layer | Technology |
|-------|------------|
| Backend | Django 5.x, Django REST Framework |
| AI | LangChain, Ollama (local LLM) |
| Database | SQLite (dev), PostgreSQL (recommended for prod) |
| Containerization | Docker, docker‑compose |
| CI/CD | GitHub Actions (`.github/workflows/ci.yml`) |
| Testing | pytest, Django test framework |

---

## Installation  

```bash
# Clone the repository
git clone https://github.com/jammyjam-j/django-ai-marketplace

cd django-ai-marketplace

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy the example env file and edit it
cp .env.example .env
# Edit .env to set DATABASE_URL, OLLAMA_URL, etc.

# Apply migrations and seed data
python manage.py migrate
python scripts/seed_products.py

# Run the development server
python manage.py runserver
```

**Docker**  
```bash
docker compose up --build
```
The web app will be available at `http://localhost:8000`. The Ollama container automatically starts and listens on port `11434`.

---

## Usage Examples  

### 1. View product list (web UI)

Navigate to `http://localhost:8000/` – a simple catalogue page lists all products.

### 2. Product detail with AI recommendations

```html
<!-- templates/product_detail.html -->
{% extends "base.html" %}
{% block content %}
<h1>{{ product.title }}</h1>
<p>{{ product.description }}</p>

<h3>Recommended for you</h3>
<ul>
    {% for rec in recommended_products %}
        <li><a href="{% url 'product-detail' rec.id %}">{{ rec.title }}</a></li>
    {% empty %}
        <li>No recommendations available.</li>
    {% endfor %}
</ul>
{% endblock %}
```

The view fetches `recommended_products` via the `recommendation/recommender.py` module.

### 3. API: Get product list

```bash
curl http://localhost:8000/api/products/
```

### 4. API: Get recommendations for a product

```bash
curl http://localhost:8000/api/products/1/recommendations/
```

Response format:

```json
[
    {"id": 3, "title": "Wireless Mouse", "price": "25.00"},
    {"id": 5, "title": "USB-C Hub", "price": "40.00"}
]
```

---

## API Endpoints  

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/products/` | List all products (paginated). |
| `GET` | `/api/products/<id>/` | Retrieve a single product. |
| `POST` | `/api/products/` | Create a new product (admin only). |
| `PUT/PATCH` | `/api/products/<id>/` | Update an existing product. |
| `DELETE` | `/api/products/<id>/` | Delete a product. |
| `GET` | `/api/products/<id>/recommendations/` | Return AI‑generated related products. |

All endpoints are documented in the Swagger UI at `/swagger/` (requires installing `drf-spectacular`).

---

## References and Resources  

1. [Build AI Web Apps with Django & LangChain – Medium](https://plainenglish.io/blog/django-langchained)  
2. [E-commerce Product Recommendation System with Gen AI – GitHub](https://github.com/Abhinayareddy18/Ecommerce-recommendation-using-GenAI)  
3. [How to integrate Django with Langchain (2025) – Medium](https://medium.com/@pyplane/how-to-integrate-django-with-langchain-2025-3f37d8b5c47a)  
4. [Building a Product Recommendation System with LangChain AI](https://www.dhiwise.com/post/building-a-product-recommendation-system-with-langchain-ai)  
5. [Build a Local Product Recommendation System with LangChain, Ollama, and ... – Simplico](https://simplico.net/2025/07/23/build-a-local-product-recommendation-system-with-langchain-ollama-and-open-source-embeddings/)  

---

## Contributing  

Contributions are welcome!  
1. Fork the repository at <https://github.com/jammyjam-j/django-ai-marketplace>.  
2. Create a feature branch (`git checkout -b feature/foo`).  
3. Run tests locally: `pytest`.  
4. Submit a pull request and open an issue if you need clarification.

All PRs must pass the CI workflow before merging.

---

## License  

MIT © 2026