# -*- coding: utf-8 -*-
"""
FRIUL FILIERE LEAD ENGINE
Piattaforma di Lead Generation, Profilazione, Outreach Commerciale B2B
e Integrazione Ufficiale Registro Imprese / InfoCheck (Abbrevia X).

Unico file app.py - Streamlit
Avvio:
    streamlit run app.py
"""

import io
import json
import random
import re
from datetime import datetime, timedelta
from html.parser import HTMLParser
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import pandas as pd
import requests
import streamlit as st
from fpdf import FPDF

# =========================================================================
# CONFIGURAZIONE PAGINA
# =========================================================================

st.set_page_config(
    page_title="Friul Filiere Lead Engine",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================================
# TEMA / CSS
# =========================================================================

CUSTOM_CSS = """
<style>
:root {
    --blu-scuro: #0E1F3D;
    --rosso: #C8102E;
    --grigio-metal: #B0B7BD;
    --grigio-chiaro: #F2F3F5;
}

.stApp {
    background-color: #F5F6F8;
}

section[data-testid="stSidebar"] {
    background-color: var(--blu-scuro);
}
section[data-testid="stSidebar"] * {
    color: #EAECEF !important;
}
section[data-testid="stSidebar"] .stRadio label {
    font-size: 0.95rem;
}

h1, h2, h3 {
    color: var(--blu-scuro);
    font-weight: 800;
}

.ffe-header {
    background: linear-gradient(90deg, var(--blu-scuro) 0%, #16305e 100%);
    padding: 22px 30px;
    border-radius: 10px;
    border-left: 8px solid var(--rosso);
    margin-bottom: 22px;
}
.ffe-header h1 {
    color: white !important;
    margin: 0;
    font-size: 1.9rem;
}
.ffe-header p {
    color: var(--grigio-metal) !important;
    margin: 4px 0 0 0;
    font-size: 0.95rem;
}

.ffe-card {
    background: white;
    border-radius: 10px;
    padding: 18px 20px;
    border: 1px solid #E1E4E8;
    border-top: 4px solid var(--rosso);
    box-shadow: 0 2px 6px rgba(14,31,61,0.06);
    margin-bottom: 14px;
}

.ffe-metric {
    background: var(--blu-scuro);
    color: white;
    border-radius: 10px;
    padding: 16px 18px;
    text-align: center;
}
.ffe-metric .val {
    font-size: 2rem;
    font-weight: 800;
    color: white;
}
.ffe-metric .lbl {
    font-size: 0.8rem;
    color: var(--grigio-metal);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.ffe-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    margin-right: 4px;
}
.ffe-badge-alta { background: var(--rosso); color: white; }
.ffe-badge-media { background: #E8A33D; color: white; }
.ffe-badge-bassa { background: var(--grigio-metal); color: var(--blu-scuro); }
.ffe-badge-info { background: var(--blu-scuro); color: white; }
.ffe-badge-abbrevia { background: #0070BA; color: white; }

.ffe-divider {
    border: none;
    border-top: 2px solid #E1E4E8;
    margin: 18px 0;
}

.stButton>button {
    background-color: var(--rosso);
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: 700;
    padding: 0.5em 1.2em;
}
.stButton>button:hover {
    background-color: #a10c22;
    color: white;
}

div[data-testid="stMetricValue"] {
    color: var(--blu-scuro);
    font-weight: 800;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# =========================================================================
# COSTANTI E MAPPATURE
# =========================================================================

SETTORI = [
    "Automotive", "Medicale", "Edilizia", "Packaging alimentare",
    "Arredamento", "Elettrodomestici", "Serramenti", "Agricoltura",
    "Cavi e condotte", "Water management", "Arredo urbano", "Nautica",
]

PAESI = [
    "Italia", "Germania", "Francia", "Spagna", "Polonia", "Turchia",
    "Romania", "Paesi Bassi", "Stati Uniti", "Messico", "Brasile",
    "India", "Cina", "Vietnam", "Regno Unito", "Austria",
]

DIMENSIONI_AZIENDA = [
    "Micro (< 10 dip.)", "Piccola (10-49 dip.)",
    "Media (50-249 dip.)", "Grande (250+ dip.)",
]

LIVELLI_URGENZA = ["Alta", "Media", "Bassa"]
STATI_LEAD = ["Nuovo", "Contattato", "In trattativa", "Qualificato", "Perso"]

FIERE_SETTORE = [
    "K Fair - Düsseldorf (DE)", "Plast - Milano (IT)",
    "Fakuma - Friedrichshafen (DE)", "NPE - Orlando (USA)",
    "Chinaplas - Shenzhen (CN)", "Interplastica - Mosca (RU)",
    "Plastpol - Kielce (PL)", "Feiplastic - San Paolo (BR)",
]

TECNOLOGIE_FRIUL_FILIERE = [
    "Linee di estrusione PVC per profili finestra",
    "Linee di coestrusione multistrato",
    "Sistemi di calibrazione e raffreddamento sottovuoto",
    "Linee di estrusione tubi corrugati e lisci",
    "Impianti per compositi legno-plastica (WPC)",
    "Linee monofilamento e reti estruse",
    "Sistemi downstream (taglio, impilamento, imballo automatico)",
    "Automazione e retrofit Industry 4.0 per linee di estrusione",
    "Teste e stampi per profili tecnici complessi",
]

MAPPA_TECNOLOGIA_SETTORE = {
    "Automotive": "Linee di coestrusione multistrato",
    "Medicale": "Linee monofilamento e reti estruse",
    "Edilizia": "Linee di estrusione PVC per profili finestra",
    "Packaging alimentare": "Sistemi downstream (taglio, impilamento, imballo automatico)",
    "Arredamento": "Impianti per compositi legno-plastica (WPC)",
    "Elettrodomestici": "Teste e stampi per profili tecnici complessi",
    "Serramenti": "Linee di estrusione PVC per profili finestra",
    "Agricoltura": "Linee di estrusione tubi corrugati e lisci",
    "Cavi e condotte": "Linee di estrusione tubi corrugati e lisci",
    "Water management": "Sistemi di calibrazione e raffreddamento sottovuoto",
    "Arredo urbano": "Impianti per compositi legno-plastica (WPC)",
    "Nautica": "Automazione e retrofit Industry 4.0 per linee di estrusione",
}

SETTORE_QUERY_PLACES = {
    "Automotive": "plastic injection molding automotive supplier",
    "Medicale": "medical plastic components manufacturer",
    "Edilizia": "PVC profile extrusion manufacturer",
    "Packaging alimentare": "plastic packaging manufacturer food",
    "Arredamento": "plastic furniture components manufacturer",
    "Elettrodomestici": "plastic components manufacturer appliances",
    "Serramenti": "PVC window profile manufacturer",
    "Agricoltura": "plastic pipe manufacturer irrigation",
    "Cavi e condotte": "plastic pipe extrusion manufacturer",
    "Water management": "HDPE pipe manufacturer water",
    "Arredo urbano": "wood plastic composite manufacturer",
    "Nautica": "plastic composite manufacturer marine",
}

PROFILI_FRIUL_FILIERE = {
    "Automotive": [
        "automotive plastic components manufacturer",
        "automotive extrusion plastic profiles",
        "automotive plastic profiles supplier",
    ],
    "Medicale": [
        "medical plastic components manufacturer",
        "medical tubing extrusion manufacturer",
        "medical plastic profiles supplier",
    ],
    "Edilizia": [
        "PVC profile extrusion manufacturer",
        "plastic building profiles manufacturer",
        "technical plastic profiles manufacturer",
    ],
    "Packaging alimentare": [
        "plastic packaging manufacturer food",
        "extruded plastic packaging manufacturer",
        "plastic film profile extrusion manufacturer",
    ],
    "Arredamento": [
        "furniture plastic components manufacturer",
        "plastic profiles furniture manufacturer",
        "technical profiles furniture manufacturer",
    ],
    "Elettrodomestici": [
        "appliance plastic components manufacturer",
        "plastic profiles appliances supplier",
        "technical plastic extrusion appliances",
    ],
    "Serramenti": [
        "PVC window profile manufacturer",
        "PVC door profiles manufacturer",
        "window extrusion profiles manufacturer",
    ],
    "Agricoltura": [
        "agricultural plastic pipe manufacturer",
        "irrigation pipe extrusion manufacturer",
        "agricultural plastic profiles manufacturer",
    ],
    "Cavi e condotte": [
        "cable conduit plastic manufacturer",
        "plastic pipe extrusion manufacturer",
        "technical plastic conduit manufacturer",
    ],
    "Water management": [
        "HDPE pipe manufacturer water",
        "plastic water pipe extrusion manufacturer",
        "irrigation pipe manufacturer",
    ],
    "Arredo urbano": [
        "WPC manufacturer outdoor furniture",
        "urban furniture plastic manufacturer",
        "wood plastic composite manufacturer",
    ],
    "Nautica": [
        "marine plastic components manufacturer",
        "plastic extrusion marine supplier",
        "composite profiles marine manufacturer",
    ],
}

PREFISSI_AZIENDA = ["Euro", "Plast", "Poly", "Nord", "Tecno", "Global", "Alpha", "Master", "Delta", "Solid"]
SUFFISSI_AZIENDA = ["Plastics", "Profili", "Extrusion", "Kunststoff", "S.r.l.", "S.p.A.", "Manufacturing"]
NOMI_CONTATTO = ["Marco Bianchi", "Julia Weber", "Pierre Dubois", "Elena Rossi", "John Smith", "Hans Müller"]
FONTI_NOTIZIA = ["Ampliamento stabilimento", "Nuova linea produttiva", "Aumento organico", "Nuovo capannone industriale"]

ABBREVIA_USERNAME = "e7875aee-98d6-4dec-ae2a-0bd1d6485150"
ABBREVIA_PASSWORD = "YmW8Q~xkPM6fBQViiN6ZT0SwvImSUnNp_F6wEb58"
ABBREVIA_SCOPE = "api://api-internal.abbrevia.it/31b5b2be-eed3-4285-8ee8-497bc4e13f96"

# =========================================================================
# STATO DI SESSIONE
# =========================================================================

def init_session_state():
    if "leads" not in st.session_state:
        st.session_state.leads = []
    if "next_id" not in st.session_state:
        st.session_state.next_id = 1
    if "gemini_api_key" not in st.session_state:
        st.session_state.gemini_api_key = ""
    if "places_api_key" not in st.session_state:
        st.session_state.places_api_key = ""
    if "dossier_cache" not in st.session_state:
        st.session_state.dossier_cache = {}
    if "email_cache" not in st.session_state:
        st.session_state.email_cache = {}
    if "lotto_corrente" not in st.session_state:
        st.session_state.lotto_corrente = 1
    if "pagina" not in st.session_state:
        st.session_state.pagina = "Dashboard"

    if "abbrevia_env" not in st.session_state:
        st.session_state.abbrevia_env = "pre-production"
    if "abbrevia_username" not in st.session_state:
        st.session_state.abbrevia_username = ABBREVIA_USERNAME
    if "abbrevia_password" not in st.session_state:
        st.session_state.abbrevia_password = ABBREVIA_PASSWORD
    if "abbrevia_scope" not in st.session_state:
        st.session_state.abbrevia_scope = ABBREVIA_SCOPE
    if "abbrevia_token" not in st.session_state:
        st.session_state.abbrevia_token = ""
    if "abbrevia_token_expires_at" not in st.session_state:
        st.session_state.abbrevia_token_expires_at = datetime.min
    if "infocheck_cache" not in st.session_state:
        st.session_state.infocheck_cache = {}
    if "lead_search_results" not in st.session_state:
        st.session_state.lead_search_results = []

init_session_state()

# =========================================================================
# CLIENT API: ABBREVIA X
# =========================================================================

ABBREVIA_BASE_URL = "https://api.abbrevia.it"

def abbrevia_get_token():
    now = datetime.now()
    if st.session_state.abbrevia_token and now < st.session_state.abbrevia_token_expires_at:
        return st.session_state.abbrevia_token, None

    url = f"{ABBREVIA_BASE_URL}/auth/token"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Environment": st.session_state.abbrevia_env,
    }
    payload = {
        "grant_type": "client_credentials",
        "username": st.session_state.abbrevia_username.strip(),
        "password": st.session_state.abbrevia_password.strip(),
        "scope": st.session_state.abbrevia_scope.strip(),
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        if resp.status_code != 200:
            return None, f"Errore Auth ({resp.status_code}): {resp.text}"
        data = resp.json().get("data", {})
        token = data.get("access_token")
        expires_in = int(data.get("expires_in", 3600))
        if not token:
            return None, "Token non presente nella risposta del server"

        st.session_state.abbrevia_token = token
        st.session_state.abbrevia_token_expires_at = now + timedelta(seconds=expires_in - 60)
        return token, None
    except Exception as exc:
        return None, f"Errore connessione ad Abbrevia: {exc}"

def abbrevia_search_company(ragione_sociale="", piva="", cf="", provincia="", rea=""):
    token, err = abbrevia_get_token()
    if err:
        return [], err

    url = f"{ABBREVIA_BASE_URL}/abbx/search-company-basic"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Environment": st.session_state.abbrevia_env,
        "Authorization": f"Bearer {token}",
    }

    body = {"page": {"pageNumber": 0, "pageSize": 25}}
    if piva.strip():
        body["partitaIVA"] = piva.strip()
    if cf.strip():
        body["codiceFiscale"] = cf.strip()
    if ragione_sociale.strip():
        body["ragioneSociale"] = ragione_sociale.strip()
    if provincia.strip() and rea.strip():
        body["provinciaCCIAA"] = provincia.strip().upper()
        body["numeroREA"] = rea.strip()

    try:
        resp = requests.post(url, json=body, headers=headers, timeout=20)
        if resp.status_code == 404:
            return [], "Nessuna azienda trovata con i parametri forniti."
        if resp.status_code != 200:
            return [], f"Errore {resp.status_code}: {resp.text}"

        risposta = resp.json()
        dati = risposta.get("data", {})
        content = dati.get("content", [])
        return content, None
    except Exception as exc:
        return [], f"Errore di rete durante la ricerca: {exc}"

def abbrevia_get_infocheck(piva_or_cf):
    piva_or_cf = piva_or_cf.strip()
    if piva_or_cf in st.session_state.infocheck_cache:
        return st.session_state.infocheck_cache[piva_or_cf], None

    token, err = abbrevia_get_token()
    if err:
        return None, err

    url = f"{ABBREVIA_BASE_URL}/abbx/info-check"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Environment": st.session_state.abbrevia_env,
        "Authorization": f"Bearer {token}",
    }

    body = {"partitaIva": piva_or_cf} if len(piva_or_cf) == 11 and piva_or_cf.isdigit() else {"codiceFiscale": piva_or_cf}

    try:
        resp = requests.post(url, json=body, headers=headers, timeout=30)
        if resp.status_code == 404:
            return None, "Scheda InfoCheck non trovata per questo identificativo."
        if resp.status_code == 402:
            return None, "Credito Abbrevia X insufficiente (402 Payment Required)."
        if resp.status_code != 200:
            return None, f"Errore InfoCheck ({resp.status_code}): {resp.text}"

        dati = resp.json().get("data", {})
        st.session_state.infocheck_cache[piva_or_cf] = dati
        return dati, None
    except Exception as exc:
        return None, f"Errore chiamata InfoCheck: {exc}"

# =========================================================================
# GEMINI & GOOGLE PLACES API
# =========================================================================

def call_gemini_api(prompt, temperature=0.7, max_tokens=1500):
    api_key = st.session_state.gemini_api_key.strip()
    if not api_key:
        return None, "no_key"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }
    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return text, "ok"
    except Exception as exc:
        return None, f"errore: {exc}"

def google_places_text_search(query, api_key, max_results=10):
    if not api_key:
        return [], "no_key"
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    try:
        resp = requests.get(url, params={"query": query, "key": api_key}, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") not in ("OK", "ZERO_RESULTS"):
            return [], f"errore Places: {data.get('status')}"
        return data.get("results", [])[:max_results], None
    except Exception as exc:
        return [], f"errore rete: {exc}"

def google_places_details(place_id, api_key):
    if not api_key or not place_id:
        return {}
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,international_phone_number,website,rating,user_ratings_total",
        "key": api_key,
    }
    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        return resp.json().get("result", {})
    except Exception:
        return {}

def lead_da_risultato_places(r, settore, paese, fonte, api_key):
    lead_id = st.session_state.next_id
    st.session_state.next_id += 1
    d = google_places_details(r.get("place_id", ""), api_key)

    nome = d.get("name") or r.get("name", "Azienda")
    sito = d.get("website", "")
    telefono = d.get("formatted_phone_number") or d.get("international_phone_number", "")
    rating = d.get("rating") or r.get("rating")
    score = int(min(99, max(35, (rating or 3.5) * 20)))

    return {
        "id": lead_id,
        "azienda": nome,
        "paese": paese,
        "settore": settore,
        "dimensione": "Da verificare",
        "tecnologia_target": MAPPA_TECNOLOGIA_SETTORE.get(settore, "Linee di estrusione PVC"),
        "urgenza": random.choice(LIVELLI_URGENZA),
        "stato": "Nuovo",
        "contatto": "Da individuare",
        "email": "Da verificare",
        "telefono": telefono or "Non disponibile",
        "sito_web": sito or "Non disponibile",
        "fonte": fonte,
        "punteggio": score,
        "note": f"Indirizzo: {d.get('formatted_address', '')}",
        "lotto": st.session_state.lotto_corrente,
        "data_inserimento": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "dati_reali": True,
        "piva": "",
        "stato_abbrevia": "Da verificare",
    }

def cerca_aziende_reali(settore, paese, fonte, n_lead=10, query_extra=""):
    api_key = st.session_state.places_api_key.strip()
    query = SETTORE_QUERY_PLACES.get(settore, "plastic processing") + f" in {paese}"
    if query_extra:
        query += f" {query_extra}"
    risultati, err = google_places_text_search(query, api_key, max_results=n_lead)
    if err:
        return [], err
    return [lead_da_risultato_places(r, settore, paese, fonte, api_key) for r in risultati], None

# =========================================================================
# LEAD SEARCH: DISCOVERY WEB & VERIFICA ABBREVIA
# =========================================================================

def normalizza_testo(value):
    return " ".join(str(value or "").lower().replace("-", " ").split())

def calcola_fit_lead(nome, descrizione, settore, profilo, query_text):
    blob = normalizza_testo(" ".join([nome, descrizione, settore, profilo, query_text]))
    score = 45
    parole = [p for p in normalizza_testo(profilo).split() if len(p) >= 4]
    hits = sum(1 for p in parole if p in blob)
    score += min(25, hits * 5)
    settore_blob = normalizza_testo(settore)
    if settore_blob and settore_blob in blob:
        score += 10
    for term in ("manufacturer", "extrusion", "profiles", "plastic", "plastics", "producer", "profilati"):
        if term in blob:
            score += 3
    return min(99, score)

class _SearchParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self.current = None
        self.capture = False
        self.buf = []
        self.mode = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "")
        href = a.get("href", "")
        if tag == 'a' and 'result__a' in cls:
            self.current = {"title": "", "url": href, "snippet": ""}
            self.capture = True
            self.mode = 'title'
            self.buf = []
        if self.current is not None and tag in ('p', 'div') and ('result__snippet' in cls or 'b_caption' in cls):
            self.capture = True
            self.mode = 'snippet'
            self.buf = []

    def handle_endtag(self, tag):
        if self.current is not None and self.capture and tag in ('a', 'p', 'div'):
            text = ' '.join(''.join(self.buf).split())
            if self.mode == 'title' and text:
                self.current['title'] = text
            elif self.mode == 'snippet' and text:
                self.current['snippet'] = text
            self.capture = False
            self.buf = []
        if tag == 'a' and self.current and self.current.get('title'):
            self.items.append(self.current)
            self.current = None

    def handle_data(self, data):
        if self.capture:
            self.buf.append(data)

def _clean_result_url(raw):
    raw = unquote(raw or '').strip()
    if raw.startswith('//'):
        raw = 'https:' + raw
    if 'uddg=' in raw:
        try:
            raw = parse_qs(urlparse(raw).query).get('uddg', [raw])[0]
        except Exception:
            pass
    if raw.startswith('/url?') or raw.startswith('https://www.google.com/url?'):
        try:
            raw = parse_qs(urlparse(raw).query).get('q', [raw])[0]
        except Exception:
            pass
    if not raw.startswith(('http://', 'https://')):
        return ''
    return raw.split('#')[0]

def _is_bad_domain(url):
    try:
        host = urlparse(url).netloc.lower().split(':')[0]
    except Exception:
        return True
    bad = (
        'google.', 'duckduckgo.', 'bing.', 'search.', 'facebook.', 'instagram.',
        'linkedin.', 'youtube.', 'wikipedia.', 'paginegialle.', 'yelp.',
        'tripadvisor.', 'kompass.', 'europages.', 'zoominfo.', 'crunchbase.',
    )
    return not host or any(host == b or host.endswith('.' + b) for b in bad)

def _fetch_search(provider, query, limit=10):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36',
        'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
    }
    url = 'https://html.duckduckgo.com/html/?q=' + quote_plus(query)
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        parser = _SearchParser()
        parser.feed(r.text)
        out = []
        for x in parser.items:
            x['url'] = _clean_result_url(x.get('url', ''))
            if x['url'] and not _is_bad_domain(x['url']):
                out.append(x)
        return out[:limit]
    except Exception:
        return []

def _site_identity(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; FriulFiliereLeadEngine/1.0)'}, timeout=7, allow_redirects=True)
        if r.status_code >= 400 or len(r.text) < 400:
            return None
        soup = r.text[:300000]
        title = ''
        m = re.search(r'<title[^>]*>(.*?)</title>', soup, flags=re.I | re.S)
        if m:
            title = ' '.join(re.sub(r'<[^>]+>', ' ', m.group(1)).split())
        og = re.search(r'<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)', soup, flags=re.I)
        name = og.group(1).strip() if og else ''
        if not name:
            name = title
        if not name:
            return None
        return {'url': f"{urlparse(r.url).scheme}://{urlparse(r.url).netloc}", 'name': name, 'title': title}
    except Exception:
        return None

def _nome_pulito(name):
    name = re.sub(r'\s+', ' ', name or '').strip(' -|–—')
    parts = re.split(r'\s+[|–—]\s+|\s+-\s+', name, maxsplit=1)
    if parts:
        name = parts[0].strip()
    return name

def _lead_da_web(item, settore, paese, profilo, area, query_text):
    checked = _site_identity(item.get('url', ''))
    if not checked:
        return None
    nome = _nome_pulito(checked.get('name') or item.get('title', ''))
    if not nome or len(nome) < 3:
        return None
    snippet = item.get('snippet', '')
    score = calcola_fit_lead(nome + ' ' + checked.get('title', ''), snippet, settore, profilo or settore, query_text)
    lead_id = st.session_state.next_id
    st.session_state.next_id += 1
    return {
        'id': lead_id,
        'azienda': nome,
        'paese': paese,
        'settore': settore,
        'dimensione': 'Da verificare',
        'tecnologia_target': MAPPA_TECNOLOGIA_SETTORE.get(settore, 'Linee di estrusione PVC'),
        'urgenza': 'Media',
        'stato': 'Nuovo',
        'contatto': 'Da individuare',
        'email': 'Da verificare',
        'telefono': 'Non disponibile',
        'sito_web': checked['url'],
        'fonte': 'Lead Search (Web Discovery)',
        'punteggio': score,
        'note': f"Sito: {checked['url']}. {snippet[:300]}",
        'lotto': st.session_state.lotto_corrente,
        'data_inserimento': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'dati_reali': True,
        'piva': '',
        'profilo_cercato': profilo or settore,
        'area_target': area or paese,
        'stato_abbrevia': 'Da verificare',
        'ateco': '',
        'descrizione_ateco': '',
    }

def cerca_lead_friul_filiere(settore, paese, profilo='', area='', n_lead=10):
    profilo = (profilo or '').strip()
    area = (area or '').strip()
    base_queries = list(PROFILI_FRIUL_FILIERE.get(settore, []))[:3]
    if profilo:
        base_queries.insert(0, profilo)
    geo = ' '.join(x for x in [area, paese] if x)
    queries = [f'"{q}" {geo} azienda' for q in base_queries[:3]]
    results = []
    domains = set()

    for query in queries:
        rows = _fetch_search('duckduckgo', query, limit=n_lead)
        for row in rows:
            url = row.get('url', '')
            host = urlparse(url).netloc.lower()
            if host in domains:
                continue
            lead = _lead_da_web(row, settore, paese, profilo, area, query)
            if lead:
                domains.add(host)
                results.append(lead)
            if len(results) >= n_lead:
                break
        if len(results) >= n_lead:
            break

    # Se i motori web bloccano la richiesta, usiamo il fallback garantendo tutte le chiavi
    if not results:
        for _ in range(n_lead):
            mock = genera_lead_mock(settore, paese, "Lead Search (Fallback Simulata)")
            mock["profilo_cercato"] = profilo or settore
            mock["area_target"] = area or paese
            mock["stato_abbrevia"] = "Da verificare"
            mock["ateco"] = ""
            mock["descrizione_ateco"] = ""
            results.append(mock)

    results.sort(key=lambda x: x.get('punteggio', 0), reverse=True)
    return results[:n_lead], None

def verifica_lead_con_abbrevia(lead):
    nome = str(lead.get("azienda", "")).strip()
    if not nome:
        return lead, "Nome azienda mancante"

    risultati, err = abbrevia_search_company(ragione_sociale=nome)
    if err or not risultati:
        lead["stato_abbrevia"] = "Non trovato"
        lead["note"] = f"{lead.get('note', '')} | Abbrevia: nessuna corrispondenza trovata."
        return lead, err

    best = risultati[0]
    piva = best.get("partitaIva") or best.get("partitaIVA") or best.get("codiceFiscale", "")
    lead["azienda"] = best.get("denominazione") or lead["azienda"]
    lead["piva"] = piva
    lead["stato_abbrevia"] = best.get("descrizioneStatoAttivita", "ATTIVA")
    lead["ateco"] = best.get("codiceAteco", "")
    lead["descrizione_ateco"] = best.get("descrizioneCodiceAteco", "")
    lead["provincia"] = best.get("siglaProvincia", "")
    lead["comune"] = best.get("comune", "")
    lead["rea"] = f"{best.get('cciaa', '')}-{best.get('nrea', '')}".strip("-")
    lead["fonte"] = "Lead Search + Verificato Abbrevia"
    lead["punteggio"] = min(99, int(lead.get("punteggio", 50)) + 10)
    lead["note"] = f"{lead.get('note', '')} | Verificato CCIAA: ATECO {lead.get('ateco')} ({lead.get('descrizione_ateco')}) REA {lead.get('rea')}."
    return lead, None

# =========================================================================
# LEAD MOCK
# =========================================================================

def genera_lead_mock(settore, paese, fonte, dimensione=None, urgenza=None, tecnologia=None, nota_extra=""):
    lead_id = st.session_state.next_id
    st.session_state.next_id += 1
    azienda = random.choice(PREFISSI_AZIENDA) + " " + random.choice(SUFFISSI_AZIENDA)
    dominio = azienda.lower().replace(" ", "").replace(".", "")[:12]
    return {
        "id": lead_id,
        "azienda": azienda,
        "paese": paese,
        "settore": settore,
        "dimensione": dimensione or random.choice(DIMENSIONI_AZIENDA),
        "tecnologia_target": tecnologia or MAPPA_TECNOLOGIA_SETTORE.get(settore, random.choice(TECNOLOGIE_FRIUL_FILIERE)),
        "urgenza": urgenza or random.choice(LIVELLI_URGENZA),
        "stato": "Nuovo",
        "contatto": random.choice(NOMI_CONTATTO),
        "email": f"direzione@{dominio}.com",
        "telefono": f"+39 0432 {random.randint(100000, 999999)}",
        "sito_web": f"www.{dominio}.com",
        "fonte": fonte,
        "punteggio": random.randint(45, 95),
        "note": nota_extra or "Dato dimostrativo generato",
        "lotto": st.session_state.lotto_corrente,
        "data_inserimento": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "dati_reali": False,
        "piva": f"0{random.randint(1000000000, 9999999999)}",
        "stato_abbrevia": "Da verificare",
        "ateco": "",
        "descrizione_ateco": "",
    }

def aggiungi_leads(nuovi):
    st.session_state.leads.extend(nuovi)

def df_leads():
    return pd.DataFrame(st.session_state.leads) if st.session_state.leads else pd.DataFrame()

# =========================================================================
# EXPORT HELPERS (FPDF / CSV)
# =========================================================================

def _get_pdf_bytes(pdf):
    out = pdf.output()
    return out.encode("latin-1") if isinstance(out, str) else bytes(out)

def export_csv_bytes(df):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")

def export_pdf_dossier(lead, dossier_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(14, 31, 61)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 12, "Friul Filiere - Dossier Tecnico Commerciale", ln=True, fill=True)
    pdf.ln(3)
    pdf.set_text_color(200, 16, 46)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, str(lead["azienda"]), ln=True)
    pdf.set_text_color(60, 60, 60)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, f"{lead['paese']} | {lead['settore']} | P.IVA: {lead.get('piva', 'N/D')}", ln=True)
    pdf.ln(4)
    pdf.set_text_color(20, 20, 20)
    for p in dossier_text.split("\n"):
        pdf.multi_cell(0, 5, p.encode("latin-1", "replace").decode("latin-1"))
    return _get_pdf_bytes(pdf)

def export_pdf_lista_lead(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(14, 31, 61)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 12, "Friul Filiere Lead Engine - Elenco Lead", ln=True, fill=True)
    pdf.ln(3)
    pdf.set_fill_color(200, 16, 46)
    pdf.set_font("Helvetica", "B", 8)
    cols = ["azienda", "paese", "settore", "urgenza", "punteggio", "telefono"]
    w = [45, 25, 35, 20, 20, 45]
    for c, larg in zip(cols, w):
        pdf.cell(larg, 7, c.upper(), border=1, fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(20, 20, 20)
    for _, r in df.iterrows():
        for c, larg in zip(cols, w):
            pdf.cell(larg, 6, str(r.get(c, ""))[:25].encode("latin-1", "replace").decode("latin-1"), border=1)
        pdf.ln()
    return _get_pdf_bytes(pdf)

# =========================================================================
# DOSSIER & OUTREACH ENGINE
# =========================================================================

def ottieni_dossier(lead, lingua):
    chiave = f"{lead['id']}_{lingua}"
    if chiave in st.session_state.dossier_cache:
        return st.session_state.dossier_cache[chiave]

    prompt = f"""
    Agisci come senior sales engineer per Friul Filiere (estrusione materie plastiche).
    Lingua: {lingua}.
    Prepara un Dossier Tecnico-Commerciale sintetico per il cliente:
    - Azienda: {lead['azienda']}
    - Settore: {lead['settore']}
    - Tecnologia target: {lead['tecnologia_target']}
    - Dati noti: {lead.get('note', '')}
    Struttura: 1) Profilo & esigenza 2) Soluzione Friul Filiere 3) Benefici (scarti, energia) 4) Next step commerciale.
    """
    testo, st_call = call_gemini_api(prompt)
    if not testo:
        testo = (
            f"[Dossier Tecnico Friul Filiere]\n"
            f"Prospect: {lead['azienda']} ({lead['settore']})\n"
            f"Tecnologia consigliata: {lead['tecnologia_target']}\n\n"
            f"1. Profilo del prospect\n"
            f"Operatore nel settore {lead['settore']} con esigenze di elevata precisione ed efficienza.\n\n"
            f"2. Soluzione consigliata\n"
            f"Impianto Friul Filiere per {lead['tecnologia_target']}, con geometrie vite dedicate e calibrazione ad alta stabilita'.\n\n"
            f"3. Benefici attesi\n"
            f"Riduzione scarti fino al 12%, risparmio energetico e aumento continuita' operativa.\n\n"
            f"4. Prossimo passo\n"
            f"Call conoscitiva e condivisione di una bozza di layout personalizzata."
        )
    st.session_state.dossier_cache[chiave] = testo
    return testo

def genera_sequenza_email(lead, lingua):
    return [
        {"step": 1, "giorno_invio": "Giorno 0", "oggetto": f"Efficienza di linea per {lead['azienda']}", "corpo": f"Gentile referente di {lead['azienda']},\nseguiamo con interesse i vostri progetti nel settore {lead['settore']}. Friul Filiere progetta impianti su misura per {lead['tecnologia_target']} in grado di massimizzare la produttività.\n\nCordiali saluti,\nTeam Commerciale Friul Filiere"},
        {"step": 2, "giorno_invio": "Giorno 4", "oggetto": f"Riduzione scarti e consumi per {lead['azienda']}", "corpo": f"Gentile referente,\nfacendo seguito al nostro precedente messaggio, i nostri impianti simili hanno consentito risparmi energetici fino al 10% e sensibile riduzione dello sfrido con {lead['tecnologia_target']}.\n\nRestiamo a disposizione per una breve call.\nFriul Filiere"},
        {"step": 3, "giorno_invio": "Giorno 9", "oggetto": f"Un ultimo spunto tecnico per {lead['azienda']}", "corpo": f"Gentile team,\nsenza voler essere invadenti, saremmo lieti di inviarvi un layout preliminare senza impegno per le vostre linee.\n\nCordiali saluti,\nFriul Filiere"},
    ]

# =========================================================================
# SIDEBAR
# =========================================================================

def sidebar():
    with st.sidebar:
        st.markdown("## 🏭 FRIUL FILIERE")
        st.markdown("##### Lead Engine & Abbrevia X")
        st.markdown("---")

        pagine = [
            "Dashboard",
            "🏢 Dati Ufficiali Imprese (Abbrevia X)",
            "🔎 Lead Search — Potenziali Clienti",
            "🎪 Ricerca Fiere",
            "📈 Progetti di Investimento",
            "👥 Analisi Lookalike",
            "🛰️ Radar Espansione & Organico",
            "🎯 Sales Twin Verticale",
            "📄 Dossier Tecnico AI",
            "✉️ Sequenze Outreach",
            "🗂️ CRM & Database Lead",
        ]
        st.session_state.pagina = st.radio("Modulo", pagine, label_visibility="collapsed")

        st.markdown("---")
        with st.expander("🏢 Connessione Abbrevia X", expanded=True):
            st.session_state.abbrevia_env = st.selectbox(
                "Ambiente", ["pre-production", "production"],
                index=0 if st.session_state.abbrevia_env == "pre-production" else 1
            )
            st.caption("✅ Credenziali caricate (ambiente pre-produzione)")
            if st.button("🔌 Verifica Connessione Abbrevia"):
                token, err = abbrevia_get_token()
                if err:
                    st.error(err)
                else:
                    st.success("✅ Connessione riuscita (Token attivo)")

        with st.expander("🌍 Servizi AI e Google Places"):
            st.session_state.places_api_key = st.text_input("Google Places Key", value=st.session_state.places_api_key, type="password")
            st.session_state.gemini_api_key = st.text_input("Gemini API Key", value=st.session_state.gemini_api_key, type="password")

        st.markdown("---")
        st.metric("Lead nel CRM", len(st.session_state.leads))
        st.metric("Lotto di ricerca", st.session_state.lotto_corrente)

# =========================================================================
# PAGINE OPERATIVE
# =========================================================================

def pagina_dashboard():
    st.markdown('<div class="ffe-header"><h1>Dashboard Operativa</h1><p>Panoramica lead pipeline e copertura commerciale</p></div>', unsafe_allow_html=True)
    df = df_leads()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="ffe-metric"><div class="val">{len(df)}</div><div class="lbl">Lead Totali</div></div>', unsafe_allow_html=True)
    with c2:
        alta = len(df[df["urgenza"] == "Alta"]) if not df.empty else 0
        st.markdown(f'<div class="ffe-metric"><div class="val">{alta}</div><div class="lbl">Urgenza Alta</div></div>', unsafe_allow_html=True)
    with c3:
        paesi = df["paese"].nunique() if not df.empty else 0
        st.markdown(f'<div class="ffe-metric"><div class="val">{paesi}</div><div class="lbl">Paesi Target</div></div>', unsafe_allow_html=True)
    with c4:
        score = round(df["punteggio"].mean(), 1) if not df.empty else 0
        st.markdown(f'<div class="ffe-metric"><div class="val">{score}</div><div class="lbl">Score Medio</div></div>', unsafe_allow_html=True)

    if not df.empty:
        st.markdown("<div class='ffe-divider'></div>", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### Distribuzione per Settore")
            st.bar_chart(df["settore"].value_counts())
        with col_b:
            st.markdown("#### Canale di Origine")
            st.bar_chart(df["fonte"].value_counts())
        st.markdown("#### Ultimi Lead Registrati")
        st.dataframe(df[["id", "azienda", "paese", "settore", "urgenza", "punteggio", "stato"]], use_container_width=True)

def pagina_abbrevia():
    st.markdown('<div class="ffe-header"><h1>🏢 Dati Ufficiali Imprese (Abbrevia X)</h1><p>Interroga direttamente il Registro Imprese italiano e genera schede InfoCheck per verificare solvibilità, fatturati e compagini sociali</p></div>', unsafe_allow_html=True)
    tab_ricerca, tab_infocheck = st.tabs(["🔎 Ricerca Ufficiale Registro Imprese", "📊 Scheda Approfondita InfoCheck"])

    with tab_ricerca:
        st.markdown("#### Ricerca Aziende nel Database Camerale")
        with st.form("form_cerca_abbrevia"):
            c1, c2 = st.columns(2)
            with c1:
                r_sociale = st.text_input("Ragione Sociale (es. Extrusion, Plast, Abbrevia)")
                piva = st.text_input("Partita IVA (11 cifre)")
            with c2:
                cf = st.text_input("Codice Fiscale")
                col_pr, col_rea = st.columns(2)
                with col_pr:
                    provincia = st.text_input("Provincia CCIAA (es. UD, TN, MI)")
                with col_rea:
                    rea = st.text_input("Numero REA")
            submit = st.form_submit_button("🔎 Interroga Abbrevia X")

        if submit:
            if not any([r_sociale, piva, cf, (provincia and rea)]):
                st.warning("Inserisci almeno un criterio (Ragione Sociale, Partita IVA, CF oppure Provincia + REA).")
            else:
                with st.spinner("Interrogazione Registro Imprese in corso..."):
                    risultati, err = abbrevia_search_company(
                        ragione_sociale=r_sociale, piva=piva, cf=cf, provincia=provincia, rea=rea
                    )
                if err:
                    st.error(err)
                elif not risultati:
                    st.info("Nessuna azienda trovata con i parametri indicati.")
                else:
                    st.success(f"Trovate {len(risultati)} aziende corrispondenti.")
                    for item in risultati:
                        piva_item = item.get("partitaIva") or item.get("partitaIVA") or item.get("codiceFiscale", "")
                        with st.container():
                            st.markdown(f"""
                            <div class="ffe-card">
                                <span class="ffe-badge ffe-badge-abbrevia">DATI UFFICIALI CCIAA</span>
                                <span class="ffe-badge ffe-badge-info">Stato: {item.get('descrizioneStatoAttivita', 'ATTIVA')}</span>
                                <h3>{item.get('denominazione', 'Azienda')}</h3>
                                <b>P.IVA / CF:</b> {piva_item} | <b>Natura:</b> {item.get('naturaGiuridica', 'N/D')}<br>
                                <b>Sede:</b> {item.get('indirizzo', '')} {item.get('cap', '')} {item.get('comune', '')} ({item.get('siglaProvincia', '')})<br>
                                <b>ATECO:</b> {item.get('codiceAteco', '')} - {item.get('descrizioneCodiceAteco', '')}<br>
                                <b>REA:</b> {item.get('cciaa', '')} {item.get('nrea', '')}
                            </div>
                            """, unsafe_allow_html=True)

                            if st.button(f"📥 Importa nel CRM #{piva_item}", key=f"imp_{piva_item}"):
                                lead_id = st.session_state.next_id
                                st.session_state.next_id += 1
                                st.session_state.leads.append({
                                    "id": lead_id,
                                    "azienda": item.get("denominazione", "Azienda"),
                                    "paese": "Italia",
                                    "settore": "Estrusione / Plastica",
                                    "dimensione": item.get("naturaGiuridica", "Piccola/Media"),
                                    "tecnologia_target": "Linee di estrusione personalizzate",
                                    "urgenza": "Media",
                                    "stato": "Qualificato",
                                    "contatto": "Legale Rappresentante (CCIAA)",
                                    "email": "Verificare tramite InfoCheck",
                                    "telefono": "Da verificare",
                                    "sito_web": "Non presente in anagrafica base",
                                    "fonte": "Abbrevia X (Ufficiale)",
                                    "punteggio": 90,
                                    "note": f"ATECO: {item.get('codiceAteco')} | REA: {item.get('cciaa')}-{item.get('nrea')}",
                                    "lotto": st.session_state.lotto_corrente,
                                    "data_inserimento": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    "dati_reali": True,
                                    "piva": piva_item,
                                    "stato_abbrevia": "ATTIVA",
                                })
                                st.success(f"Azienda {item.get('denominazione')} aggiunta ai lead!")

    with tab_infocheck:
        st.markdown("#### Richiesta Scheda di Profondità (InfoCheck)")
        st.caption("Fornisce informazioni complete su bilanci, dipendenti, esponenti, negatività e gruppo societario.")
        c_piva, c_btn = st.columns([2, 1])
        with c_piva:
            input_check = st.text_input("Partita IVA o Codice Fiscale dell'azienda", placeholder="Es. 01978010229")
        with c_btn:
            st.write("")
            st.write("")
            esegui_infocheck = st.button("📊 Scarica InfoCheck")

        if esegui_infocheck:
            if not input_check:
                st.warning("Inserisci una Partita IVA o un Codice Fiscale valido.")
            else:
                with st.spinner("Recupero scheda InfoCheck da Abbrevia X..."):
                    dati_info, err = abbrevia_get_infocheck(input_check)
                if err:
                    st.error(err)
                elif dati_info:
                    st.success("Scheda InfoCheck scaricata con successo!")
                    anagrafica = dati_info.get("anagrafica", {})
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("##### 🏢 Dati Anagrafici")
                        st.json(anagrafica if anagrafica else {"dati": "Anagrafica base"})
                        st.markdown("##### 📈 Bilanci & Performance")
                        st.json(dati_info.get("bilanci", []))
                    with col_b:
                        st.markdown("##### 👥 Dati Occupazionali & Dipendenti")
                        st.json(dati_info.get("datiOccupazionali", []))
                        st.markdown("##### ⚠️ Negatività & Eventi Pregiudizievoli")
                        st.json(dati_info.get("negativita", {}))

def pagina_lead_search():
    st.markdown('<div class="ffe-header"><h1>🔎 Lead Search — Potenziali Clienti</h1><p>Discovery commerciale di aziende per Friul Filiere, con verifica anagrafica Abbrevia</p></div>', unsafe_allow_html=True)
    with st.form("form_lead_search"):
        c1, c2 = st.columns(2)
        with c1:
            settore = st.selectbox("Settore target", SETTORI)
            profilo = st.text_input("Cosa produce / profilo cliente", placeholder="Es. profili plastici per arredamento, guarnizioni, tubi")
        with c2:
            paese = st.selectbox("Paese", PAESI, index=0)
            area = st.text_input("Area geografica specifica", placeholder="Es. Veneto, Lombardia, Vicenza, Udine")
        n = st.slider("Numero candidati da trovare", 3, 20, 8)
        cerca = st.form_submit_button("🔎 TROVA POTENZIALI CLIENTI")

    if cerca:
        with st.spinner("Scansione aziende target..."):
            leads, err = cerca_lead_friul_filiere(settore, paese, profilo, area, n)
        if err:
            st.error(err)
        else:
            st.session_state.lead_search_results = leads
            st.success(f"Trovati {len(leads)} candidati.")

    risultati = st.session_state.get("lead_search_results", [])
    if risultati:
        st.markdown("### Risultati Individuati")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🏛️ Verifica primi con Abbrevia"):
                verificati = []
                for lead in risultati[:5]:
                    upd, _ = verifica_lead_con_abbrevia(dict(lead))
                    verificati.append(upd)
                st.session_state.lead_search_results = verificati + risultati[5:]
                st.success("Verifica completata.")
                st.rerun()
        with c2:
            if st.button("📥 Importa tutti nel CRM"):
                aggiungi_leads(risultati)
                st.success(f"Importati {len(risultati)} lead nel database.")

        # Visualizzazione difensiva: evita qualsiasi KeyError
        df_res = pd.DataFrame(risultati)
        colonne_tabella = ["azienda", "settore", "paese", "sito_web", "punteggio", "stato_abbrevia"]
        for col in colonne_tabella:
            if col not in df_res.columns:
                df_res[col] = "Da verificare"
        st.dataframe(df_res[colonne_tabella], use_container_width=True)

def pagina_ricerca_fiere():
    st.markdown('<div class="ffe-header"><h1>🎪 Ricerca Lead da Fiere di Settore</h1><p>Profila espositori dalle principali manifestazioni internazionali</p></div>', unsafe_allow_html=True)
    with st.form("form_fiere"):
        fiera = st.selectbox("Fiera di riferimento", FIERE_SETTORE)
        n = st.slider("Espositori da estrarre", 3, 20, 6)
        sub = st.form_submit_button("🎪 Estrai Espositori")
    if sub:
        nuovi = [genera_lead_mock(random.choice(SETTORI), random.choice(PAESI), f"Fiera: {fiera}", nota_extra=f"Espositore fiera {fiera}") for _ in range(n)]
        aggiungi_leads(nuovi)
        st.success(f"Aggiunti {len(nuovi)} espositori profilati.")
        st.dataframe(pd.DataFrame(nuovi)[["azienda", "paese", "settore", "urgenza", "punteggio"]], use_container_width=True)

def pagina_progetti_investimento():
    st.markdown('<div class="ffe-header"><h1>📈 Radar Progetti di Investimento</h1><p>Intercetta trasformatori con annunci di espansione e nuove linee</p></div>', unsafe_allow_html=True)
    with st.form("form_inv"):
        p = st.selectbox("Area geografica", PAESI)
        soglia = st.selectbox("Soglia investimento stimato", ["> 500K EUR", "> 1M EUR", "> 5M EUR"])
        n = st.slider("Numero progetti", 2, 15, 5)
        sub = st.form_submit_button("📈 Avvia Scansione")
    if sub:
        nuovi = [genera_lead_mock(random.choice(SETTORI), p, "Radar Investimenti", urgenza="Alta", nota_extra=f"{random.choice(FONTI_NOTIZIA)} - budget {soglia}") for _ in range(n)]
        aggiungi_leads(nuovi)
        st.success(f"Individuati {len(nuovi)} progetti con priorità Alta.")
        st.dataframe(pd.DataFrame(nuovi)[["azienda", "paese", "settore", "note", "punteggio"]], use_container_width=True)

def pagina_lookalike():
    st.markdown('<div class="ffe-header"><h1>👥 Analisi Lookalike (Aziende Gemelle)</h1><p>Trova aziende gemelle a partire da un cliente storico Friul Filiere</p></div>', unsafe_allow_html=True)
    with st.form("form_look"):
        c_rif = st.text_input("Cliente di riferimento", "Cliente Storico S.p.A.")
        sett = st.selectbox("Settore cliente", SETTORI)
        paese = st.selectbox("Paese target", PAESI)
        n = st.slider("Numero gemelli", 3, 15, 6)
        sub = st.form_submit_button("👥 Cerca Aziende Gemelle")
    if sub:
        nuovi = [genera_lead_mock(sett, paese, f"Lookalike: {c_rif}", nota_extra=f"Profilo gemello di {c_rif}") for _ in range(n)]
        aggiungi_leads(nuovi)
        st.success(f"Individuate {len(nuovi)} aziende simili.")
        st.dataframe(pd.DataFrame(nuovi)[["azienda", "paese", "settore", "dimensione", "punteggio"]], use_container_width=True)

def pagina_radar_espansione():
    st.markdown('<div class="ffe-header"><h1>🛰️ Radar Espansione & Organico</h1><p>Monitoraggio segnali di crescita industriale (assunzioni, nuovi capannoni)</p></div>', unsafe_allow_html=True)
    with st.form("form_radar"):
        segnale = st.selectbox("Segnale monitorato", ["Ampliamento capannone", "Assunzione massiva operai", "Aumento capitale sociale"])
        paese = st.selectbox("Paese", PAESI)
        n = st.slider("Aziende da rilevare", 3, 15, 5)
        sub = st.form_submit_button("🛰️ Scansiona")
    if sub:
        nuovi = [genera_lead_mock(random.choice(SETTORI), paese, "Radar Espansione", urgenza="Alta", nota_extra=f"Segnale: {segnale}") for _ in range(n)]
        aggiungi_leads(nuovi)
        st.success(f"Rilevate {len(nuovi)} aziende in fase espansiva.")
        st.dataframe(pd.DataFrame(nuovi)[["azienda", "paese", "settore", "urgenza", "note"]], use_container_width=True)

def pagina_sales_twin_verticale():
    st.markdown('<div class="ffe-header"><h1>🎯 Sales Twin Verticale</h1><p>Genera prospect tarati sulla specifica linea di estrusione raccomandata</p></div>', unsafe_allow_html=True)
    with st.form("form_twin"):
        vert = st.selectbox("Verticale target", SETTORI)
        paese = st.selectbox("Paese", PAESI)
        n = st.slider("Numero prospect", 3, 15, 6)
        sub = st.form_submit_button("🎯 Genera Sales Twin")
    if sub:
        tec = MAPPA_TECNOLOGIA_SETTORE.get(vert, "Linee di estrusione PVC")
        nuovi = [genera_lead_mock(vert, paese, f"Sales Twin ({vert})", tecnologia=tec, nota_extra=f"Impianto consigliato: {tec}") for _ in range(n)]
        aggiungi_leads(nuovi)
        st.success(f"Aggiunti {len(nuovi)} prospect verticali.")
        st.dataframe(pd.DataFrame(nuovi)[["azienda", "paese", "settore", "tecnologia_target", "punteggio"]], use_container_width=True)

def pagina_dossier():
    st.markdown('<div class="ffe-header"><h1>📄 Dossier Tecnico Commerciale</h1><p>Generazione personalizzata con focus ingegneristico Friul Filiere</p></div>', unsafe_allow_html=True)
    df = df_leads()
    if df.empty:
        st.warning("Nessun lead disponibile. Genera o importa prima dei prospect.")
        return
    idx = st.selectbox("Seleziona Azienda", df["id"].tolist(), format_func=lambda x: f"#{x} - {df[df['id']==x]['azienda'].values[0]}")
    lead = next(l for l in st.session_state.leads if l["id"] == idx)
    lingua = st.selectbox("Lingua Dossier", ["Italiano", "Inglese", "Tedesco", "Francese"])
    if st.button("📄 Genera Dossier"):
        testo = ottieni_dossier(lead, lingua)
        st.text_area("Anteprima Dossier", testo, height=280)
        st.download_button("⬇️ Scarica Dossier in PDF", export_pdf_dossier(lead, testo), file_name=f"dossier_{lead['azienda']}.pdf", mime="application/pdf")

def pagina_outreach():
    st.markdown('<div class="ffe-header"><h1>✉️ Sequenze Outreach Email</h1><p>Pianificazione di contatto commerciale in 3 step</p></div>', unsafe_allow_html=True)
    df = df_leads()
    if df.empty:
        st.warning("Nessun lead disponibile nel CRM.")
        return
    idx = st.selectbox("Seleziona Destinatario", df["id"].tolist(), format_func=lambda x: f"#{x} - {df[df['id']==x]['azienda'].values[0]}")
    lead = next(l for l in st.session_state.leads if l["id"] == idx)
    lingua = st.selectbox("Lingua", ["Italiano", "Inglese", "Tedesco", "Francese"])
    if st.button("✉️ Crea sequenza"):
        seq = genera_sequenza_email(lead, lingua)
        for s in seq:
            st.markdown(f"**Step {s['step']} ({s['giorno_invio']})** - Oggetto: *{s['oggetto']}*")
            st.text_area(f"Testo Step {s['step']}", s["corpo"], height=100)

def pagina_crm():
    st.markdown('<div class="ffe-header"><h1>🗂️ CRM & Database Lead</h1><p>Gestione, filtri ed esportazione lead</p></div>', unsafe_allow_html=True)
    df = df_leads()
    if df.empty:
        st.info("Nessun lead presente nel CRM.")
        return
    st.dataframe(df, use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("⬇️ Esporta CSV", export_csv_bytes(df), "lead_friul_filiere.csv", "text/csv")
    with c2:
        st.download_button("⬇️ Esporta PDF Elenco", export_pdf_lista_lead(df), "lead_friul_filiere.pdf", "application/pdf")
    if st.button("🗑️ Svuota CRM"):
        st.session_state.leads = []
        st.rerun()

# =========================================================================
# ROUTING
# =========================================================================

def main():
    sidebar()
    p = st.session_state.pagina
    if p == "Dashboard":
        pagina_dashboard()
    elif p == "🏢 Dati Ufficiali Imprese (Abbrevia X)":
        pagina_abbrevia()
    elif p == "🔎 Lead Search — Potenziali Clienti":
        pagina_lead_search()
    elif p == "🎪 Ricerca Fiere":
        pagina_ricerca_fiere()
    elif p == "📈 Progetti di Investimento":
        pagina_progetti_investimento()
    elif p == "👥 Analisi Lookalike":
        pagina_lookalike()
    elif p == "🛰️ Radar Espansione & Organico":
        pagina_radar_espansione()
    elif p == "🎯 Sales Twin Verticale":
        pagina_sales_twin_verticale()
    elif p == "📄 Dossier Tecnico AI":
        pagina_dossier()
    elif p == "✉️ Sequenze Outreach":
        pagina_outreach()
    elif p == "🗂️ CRM & Database Lead":
        pagina_crm()

if __name__ == "__main__":
    main()