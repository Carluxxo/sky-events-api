# 🌌 API de Eventos Astronômicos

API para fornecer dados sobre próximos eventos astronômicos com informações de visibilidade e localização.

---

## 🚀 Funcionalidades

- ✅ Listagem de eventos astronômicos (eclipses, chuvas de meteoros, aproximações de asteroides)
- 📍 Informações de localização e visibilidade global
- 🔄 Atualização automática de fontes oficiais
- ⚡ Cache inteligente em memória para alta performance

---

## 🔍 APIs Utilizadas

| Fonte                | Documentação                                                              | Descrição                     |
|---------------------|---------------------------------------------------------------------------|-------------------------------|
| NASA Close Approach | [API Docs](https://ssd-api.jpl.nasa.gov/doc/cad.html)                     | Objetos próximos à Terra      |
| NASA Eclipse         | [API Docs](https://ssd-api.jpl.nasa.gov/doc/eclipse.html)                | Eclipses solares e lunares    |
| IMO Meteor Showers   | [Calendar Docs](https://www.imo.net/members/imo_calendar/)               | Chuvas de meteoros anuais     |

---

## ⚙️ Como Funciona

### 🔧 Arquitetura Principal

```
.
├── Data Fetching
│   ├── NASA Approaches
│   ├── NASA Eclipses
│   └── IMO Meteors
├── Cache Layer
│   ├── Atualização assíncrona
│   └── Ordenação por data
└── API Endpoints
    ├── /api/events
    └── /api/update
```

---

### 🔄 Fluxo de Dados

**Coleta Paralela**  
Utiliza `ThreadPoolExecutor` para buscar dados simultaneamente das 3 fontes.

**Processamento**  
- Converte diferentes formatos de data  
- Padroniza a estrutura dos eventos  
- Filtra dados inválidos

**Cache**  
- Armazena dados em memória  
- Atualiza com `/api/update` (POST)  
- Ordena por data (mais próximos primeiro)

**Entrega**  
- Formata a resposta como JSON  
- Inclui metadados de fontes e última atualização

---

## 📡 Como Consumir

### 1. Listar Todos os Eventos

```bash
curl -X GET 'http://localhost:5000/api/events'
```

**Resposta de Exemplo:**

```json
{
  "count": 42,
  "events": [
    {
      "name": "Eclipse Solar Total",
      "type": "eclipse",
      "date": "2025-10-02T00:00:00",
      "visibility": "South America",
      "coordinates": [[-120.54,43.80]],
      "source": "https://ssd-api.jpl.nasa.gov/eclipse.api"
    }
  ],
  "last_updated": "2023-08-20T15:30:00Z",
  "sources": ["NASA", "IMO"]
}
```

### 2. Forçar Atualização

```bash
curl -X POST 'http://localhost:5000/api/update'
```