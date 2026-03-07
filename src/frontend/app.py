"""
SentinelAI Box - Professional Kiosk Frontend
100% Deutsch | Touchscreen-optimiert | Fuer Kleinunternehmer

SECURITY: Alle Datenoperationen laufen ueber die Backend-API.
Kein direkter Datenbankzugriff aus dem Frontend.
"""
import streamlit as st
import os
from datetime import datetime
from html import escape as html_escape

import requests

# ============== CONFIG ==============
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="SentinelAI Box",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============== CUSTOM CSS (Touchscreen-optimiert) ==============
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Kiosk mode */
    .stApp {
        background-color: #0a0e1a;
        font-size: 18px !important;
    }

    /* Grosse Buttons fuer Touchscreen */
    .stButton > button {
        height: 60px !important;
        font-size: 20px !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
    }

    /* Primary buttons hervorheben */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
    }

    /* Tabs groesser */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        font-size: 20px !important;
        font-weight: 600;
        padding: 0 32px;
    }

    /* Metrics (Dashboard) */
    [data-testid="stMetricValue"] {
        font-size: 36px !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 18px !important;
    }

    /* Tables lesbar */
    .stDataFrame {
        font-size: 16px !important;
    }

    /* Header */
    .main-header {
        background: linear-gradient(135deg, #1a1f36 0%, #0d1117 100%);
        border: 2px solid #2d3748;
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        background: linear-gradient(90deg, #60a5fa, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem !important;
        margin: 0;
    }
    .main-header p {
        color: #94a3b8;
        font-size: 1.2rem !important;
        margin: 0.5rem 0 0 0;
    }

    /* Status badges */
    .status-badge-neu {
        background: #1e40af;
        color: #93c5fd;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 16px;
    }
    .status-badge-pruefung {
        background: #854d0e;
        color: #fbbf24;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 16px;
    }
    .status-badge-erledigt {
        background: #065f46;
        color: #6ee7b7;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 16px;
    }

    /* PII Warning Box */
    .pii-warning {
        background: #451a03;
        border: 2px solid #f59e0b;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        font-size: 18px;
    }

    /* Success Box */
    .success-box {
        background: #064e3b;
        border: 2px solid #10b981;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        font-size: 18px;
    }

    /* Document Card */
    .doc-card {
        background: #1a1f36;
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        transition: border-color 0.2s;
    }
    .doc-card:hover {
        border-color: #3b82f6;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #0f1629;
        border-right: 2px solid #1e293b;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        font-size: 20px !important;
    }
</style>
""", unsafe_allow_html=True)


# ============== API HELPER FUNCTIONS ==============

def _extract_error(resp) -> str:
    """Extract error detail from API response."""
    try:
        return resp.json().get("detail", resp.text)
    except Exception:
        return resp.text


def api_get(path: str, params: dict = None, timeout: int = 10) -> dict | list | None:
    """GET request to backend API. Returns parsed JSON or None on error."""
    try:
        resp = requests.get(f"{API_BASE}{path}", params=params, timeout=timeout)
        if 200 <= resp.status_code < 300:
            return resp.json() if resp.content else {}
        st.error(f"API-Fehler {resp.status_code}: {_extract_error(resp)}")
    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
    return None


def api_post(path: str, json_data: dict = None, timeout: int = 10) -> dict | None:
    """POST request to backend API."""
    try:
        resp = requests.post(f"{API_BASE}{path}", json=json_data, timeout=timeout)
        if 200 <= resp.status_code < 300:
            return resp.json() if resp.content else {}
        st.error(f"API-Fehler {resp.status_code}: {_extract_error(resp)}")
    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
    return None


def api_patch(path: str, json_data: dict = None, timeout: int = 10) -> dict | None:
    """PATCH request to backend API."""
    try:
        resp = requests.patch(f"{API_BASE}{path}", json=json_data, timeout=timeout)
        if 200 <= resp.status_code < 300:
            return resp.json() if resp.content else {}
        st.error(f"API-Fehler {resp.status_code}: {_extract_error(resp)}")
    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
    return None


def api_delete(path: str, timeout: int = 10) -> dict | None:
    """DELETE request to backend API."""
    try:
        resp = requests.delete(f"{API_BASE}{path}", timeout=timeout)
        if 200 <= resp.status_code < 300:
            return resp.json() if resp.content else {}
        st.error(f"API-Fehler {resp.status_code}: {_extract_error(resp)}")
    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
    return None


def check_backend_health() -> dict:
    """Check if backend is online."""
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {"status": "offline", "ollama_connected": False}


def format_status_badge(status: str) -> str:
    """Return HTML badge for document status."""
    status_map = {
        "Neu": "status-badge-neu",
        "In Pr\u00fcfung": "status-badge-pruefung",
        "Erledigt": "status-badge-erledigt",
        "Archiviert": "status-badge-erledigt"
    }
    css_class = status_map.get(status, "status-badge-neu")
    safe_status = html_escape(status)
    return f'<span class="{css_class}">{safe_status}</span>'


def safe_html(text: str) -> str:
    """Escape user-supplied text for safe HTML rendering."""
    return html_escape(str(text)) if text else ""


# ============== SIDEBAR: SYSTEM STATUS ==============

with st.sidebar:
    st.markdown("## System")
    st.markdown("---")

    health = check_backend_health()
    backend_ok = health.get("status") != "offline"
    ollama_ok = health.get("ollama_connected", False)

    if backend_ok:
        st.markdown("Backend **Online**")
    else:
        st.markdown("Backend **Offline**")

    if ollama_ok:
        st.markdown("KI **Bereit**")
    else:
        st.markdown("KI **Nicht verfuegbar**")
        if backend_ok:
            st.caption("Dokumente koennen trotzdem hochgeladen werden.")

    # Stats via API
    if backend_ok:
        stats_data = api_get("/documents/stats")
    else:
        stats_data = None

    st.markdown("---")
    st.markdown("### Datenbank")
    if stats_data:
        st.metric("Dokumente", stats_data.get("total_documents", 0))
        st.metric("PII-Faelle", stats_data.get("pii_documents", 0))
        st.metric("Audit-Eintraege", stats_data.get("audit_entries", 0))
    else:
        st.metric("Dokumente", "?")
        st.caption("Backend nicht erreichbar")

    if st.button("Aktualisieren"):
        st.rerun()


# ============== HEADER ==============

st.markdown("""
<div class="main-header">
    <h1>SentinelAI Box</h1>
    <p>Dokumenten-Management mit KI &bull; 100% Lokal &amp; DSGVO-konform</p>
</div>
""", unsafe_allow_html=True)


# ============== TABS ==============

tab_cockpit, tab_posteingang, tab_archiv = st.tabs([
    "Cockpit",
    "Posteingang",
    "Archiv"
])


# ==================== TAB A: COCKPIT ====================

with tab_cockpit:
    st.markdown("## Uebersicht")

    if not backend_ok:
        st.error(
            "Backend ist nicht erreichbar. "
            "Bitte starten Sie das System mit ./start_box.sh"
        )
    else:
        # Stats via API
        stats_data = api_get("/documents/stats") or {}
        status_counts = stats_data.get("status_counts", {})

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Offene Dokumente",
                value=status_counts.get("Neu", 0),
                help="Dokumente mit Status 'Neu'"
            )
        with col2:
            st.metric(
                label="In Pruefung",
                value=status_counts.get("In Pr\u00fcfung", 0),
                help="Dokumente werden geprueft"
            )
        with col3:
            st.metric(
                label="Erledigt",
                value=status_counts.get("Erledigt", 0),
                help="Abgeschlossene Dokumente"
            )
        with col4:
            st.metric(
                label="PII-Faelle",
                value=stats_data.get("pii_documents", 0),
                help="Dokumente mit personenbezogenen Daten"
            )

        st.markdown("---")

        # Recent documents via API
        st.markdown("### Aktuelle Dokumente")

        docs_resp = api_get("/documents/list", params={"limit": 10})
        recent_docs = docs_resp.get("documents", []) if docs_resp else []

        if recent_docs:
            for doc in recent_docs:
                doc_id = doc["id"]
                filename = safe_html(doc["filename"])
                status = doc["status"]
                uploaded = doc["uploaded_at"]
                pii = doc["pii_detected"]

                try:
                    dt = datetime.fromisoformat(uploaded)
                    time_str = dt.strftime("%d.%m.%Y %H:%M")
                except Exception:
                    time_str = safe_html(uploaded)

                pii_badge = '<span style="margin-left: 12px;">PII</span>' if pii else ''

                st.markdown(f"""
                <div class="doc-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="font-size: 18px;">{filename}</strong><br>
                            <small style="color: #94a3b8;">Hochgeladen: {time_str}</small>
                        </div>
                        <div style="text-align: right;">
                            {format_status_badge(status)}
                            {pii_badge}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_a, col_b, col_c, col_d = st.columns([1, 1, 1, 3])
                with col_a:
                    if st.button("Pruefung", key=f"pruef_{doc_id}"):
                        if api_patch(f"/documents/{doc_id}/status", {"status": "In Pr\u00fcfung"}) is not None:
                            st.rerun()
                with col_b:
                    if st.button("Erledigt", key=f"done_{doc_id}"):
                        if api_patch(f"/documents/{doc_id}/status", {"status": "Erledigt"}) is not None:
                            st.rerun()
                with col_c:
                    if st.button("Archiv", key=f"arch_{doc_id}"):
                        if api_post(f"/documents/{doc_id}/archive") is not None:
                            st.rerun()
        else:
            st.info("Noch keine Dokumente vorhanden. Nutze den Posteingang zum Hochladen.")


# ==================== TAB B: POSTEINGANG ====================

with tab_posteingang:
    st.markdown("## Posteingang")
    st.markdown("Dokumente hochladen und automatisch analysieren lassen.")

    uploaded_file = st.file_uploader(
        "Dokument auswaehlen",
        type=["pdf", "txt", "docx", "doc", "png", "jpg", "jpeg", "tiff", "tif"],
        help="Unterstuetzte Formate: PDF, TXT, DOCX, Bilder (max. 50MB)",
        label_visibility="collapsed"
    )

    if uploaded_file:
        safe_name = safe_html(uploaded_file.name)
        st.markdown(f"""
        <div class="doc-card">
            <strong>{safe_name}</strong><br>
            <small>Groesse: {uploaded_file.size / 1024:.1f} KB</small>
        </div>
        """, unsafe_allow_html=True)

        col_up1, col_up2 = st.columns([1, 3])
        with col_up1:
            upload_btn = st.button("Hochladen & Analysieren", type="primary", use_container_width=True)

        if upload_btn:
            if not backend_ok:
                st.error("Backend ist offline. Bitte starten Sie das System mit ./start_box.sh")
            else:
                with st.spinner("Dokument wird verarbeitet..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        resp = requests.post(f"{API_BASE}/documents/upload", files=files, timeout=300)

                        if resp.status_code == 413:
                            st.error("Datei ist zu gross. Maximum: 50 MB")
                            st.stop()
                        elif resp.status_code != 200:
                            st.error(f"Upload fehlgeschlagen (HTTP {resp.status_code})")
                            try:
                                err_detail = resp.json().get("detail", resp.text)
                            except Exception:
                                err_detail = resp.text
                            with st.expander("Technische Details (fuer Support)"):
                                st.code(err_detail, language="text")
                            st.stop()

                        result = resp.json()

                        doc_id = result.get("id")
                        chunks = result.get("chunk_count", 0)
                        pii_detected = result.get("pii_detected", False)
                        pii_summary = result.get("pii_summary", "")

                        st.markdown("""
                        <div class="success-box">
                            <strong>Dokument erfolgreich verarbeitet!</strong>
                        </div>
                        """, unsafe_allow_html=True)

                        col_m1, col_m2, col_m3 = st.columns(3)
                        with col_m1:
                            st.metric("Dokument-ID", doc_id[:8] + "...")
                        with col_m2:
                            st.metric("Text-Abschnitte", chunks)
                        with col_m3:
                            st.metric("PII erkannt", "Ja" if pii_detected else "Nein")

                        if pii_detected:
                            safe_pii = safe_html(pii_summary) if pii_summary else "Details nicht verfuegbar"
                            st.markdown(f"""
                            <div class="pii-warning">
                                <strong>Personenbezogene Daten erkannt:</strong><br>
                                {safe_pii}
                            </div>
                            """, unsafe_allow_html=True)

                        st.markdown("---")
                        st.markdown("### Schnellaktionen")

                        col_a1, col_a2, col_a3 = st.columns(3)
                        with col_a1:
                            if st.button("Akzeptieren & Erledigen", use_container_width=True):
                                if api_patch(f"/documents/{doc_id}/status", {"status": "Erledigt"}) is not None:
                                    st.success("Dokument als erledigt markiert!")
                                    st.rerun()
                        with col_a2:
                            if st.button("Zur Pruefung", use_container_width=True):
                                if api_patch(f"/documents/{doc_id}/status", {"status": "In Pr\u00fcfung"}) is not None:
                                    st.success("Zur Pruefung markiert!")
                                    st.rerun()
                        with col_a3:
                            if st.button("Archivieren", use_container_width=True):
                                if api_post(f"/documents/{doc_id}/archive") is not None:
                                    st.success("Archiviert!")
                                    st.rerun()

                    except requests.exceptions.ConnectionError:
                        st.error("Verbindung zum Backend fehlgeschlagen.")
                        st.info("Stellen Sie sicher, dass das Backend laeuft.")
                    except requests.exceptions.Timeout:
                        st.error("Zeitueberschreitung. Dokument zu gross oder Backend ueberlastet.")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Verbindungsfehler: {type(e).__name__}")
                    except Exception as e:
                        st.error(f"Unerwarteter Fehler: {e}")

    st.markdown("---")
    st.markdown("### Offene Dokumente (Status: Neu)")

    if backend_ok:
        new_resp = api_get("/documents/list", params={"status": "Neu", "limit": 20})
        new_docs = new_resp.get("documents", []) if new_resp else []
    else:
        new_docs = []

    if new_docs:
        for doc in new_docs:
            safe_name = safe_html(doc['filename'])
            with st.expander(f"{safe_name} -- {doc['status']}", expanded=False):
                st.write(f"**Hochgeladen:** {doc['uploaded_at']}")
                st.write(f"**PII erkannt:** {'Ja' if doc['pii_detected'] else 'Nein'}")
                if doc.get('pii_summary'):
                    st.warning(f"PII: {doc['pii_summary']}")

                col_x1, col_x2 = st.columns(2)
                with col_x1:
                    if st.button("Erledigen", key=f"finish_{doc['id']}"):
                        api_patch(f"/documents/{doc['id']}/status", {"status": "Erledigt"})
                        st.rerun()
                with col_x2:
                    if st.button("Loeschen (DSGVO)", key=f"del_{doc['id']}"):
                        result = api_delete(f"/documents/{doc['id']}")
                        if result:
                            st.success("Dokument vollstaendig geloescht (DSGVO).")
                        else:
                            st.error("Loeschung fehlgeschlagen.")
                        st.rerun()
    elif backend_ok:
        st.info("Keine offenen Dokumente.")
    else:
        st.warning("Backend nicht erreichbar.")


# ==================== TAB C: ARCHIV ====================

with tab_archiv:
    st.markdown("## Archiv & Suche")

    # Search section
    st.markdown("### Semantische Suche")

    search_query = st.text_input(
        "Suche in allen Dokumenten:",
        placeholder="z.B. 'Vertragsbedingungen' oder 'Datenschutz'",
        label_visibility="collapsed"
    )

    col_search1, col_search2 = st.columns([1, 4])
    with col_search1:
        search_k = st.number_input("Ergebnisse", 1, 20, 5, label_visibility="collapsed")
    with col_search2:
        search_btn = st.button("Suchen", type="primary", use_container_width=True)

    if search_btn and search_query.strip():
        if not backend_ok:
            st.error("Backend offline. Semantische Suche nicht verfuegbar.")
        else:
            with st.spinner("Suche laeuft..."):
                try:
                    resp = requests.get(f"{API_BASE}/api/search/quality", params={
                        "query": search_query,
                        "k": search_k
                    }, timeout=60)
                    resp.raise_for_status()
                    result = resp.json()

                    results_list = result.get("results", [])

                    if results_list:
                        st.success(f"{len(results_list)} Ergebnisse gefunden")

                        for i, res in enumerate(results_list, 1):
                            distance = res.get("distance", 1.0)
                            similarity = max(0, min(1, 1.0 - distance))
                            content = res.get("content", "")[:400]
                            metadata = res.get("metadata", {})
                            filename = safe_html(metadata.get("filename", "Unbekannt"))

                            with st.expander(f"**#{i}** {filename} -- Relevanz: {similarity:.0%}"):
                                st.markdown(content)
                                st.caption(f"Dokument-ID: {metadata.get('document_id', 'N/A')[:8]}...")
                    else:
                        st.info("Keine Ergebnisse gefunden.")

                except Exception as e:
                    st.error(f"Suche fehlgeschlagen: {e}")

    st.markdown("---")
    st.markdown("### Filter nach Status")

    col_filter1, col_filter2 = st.columns([1, 3])
    with col_filter1:
        filter_status = st.selectbox(
            "Status:",
            ["Alle", "Neu", "In Pr\u00fcfung", "Erledigt"],
            label_visibility="collapsed"
        )

    if backend_ok:
        params = {"limit": 50}
        if filter_status != "Alle":
            params["status"] = filter_status
        filtered_resp = api_get("/documents/list", params=params)
        filtered_docs = filtered_resp.get("documents", []) if filtered_resp else []
    else:
        filtered_docs = []

    st.markdown(f"**{len(filtered_docs)} Dokument(e) gefunden**")

    if filtered_docs:
        for doc in filtered_docs:
            filename = safe_html(doc['filename'])
            pii_text = 'PII erkannt' if doc['pii_detected'] else 'Keine PII'

            st.markdown(f"""
            <div class="doc-card">
                <strong style="font-size: 18px;">{filename}</strong> -- {format_status_badge(doc['status'])}<br>
                <small style="color: #94a3b8;">
                    Hochgeladen: {safe_html(doc['uploaded_at'])} |
                    {pii_text}
                </small>
            </div>
            """, unsafe_allow_html=True)

            col_z1, col_z2, col_z3 = st.columns([1, 1, 3])
            with col_z1:
                if st.button("Details", key=f"details_{doc['id']}"):
                    st.session_state[f"show_details_{doc['id']}"] = True
                    st.rerun()
            with col_z2:
                if st.button("Loeschen", key=f"delete_{doc['id']}"):
                    if st.session_state.get(f"confirm_delete_{doc['id']}", False):
                        result = api_delete(f"/documents/{doc['id']}")
                        if result:
                            st.success("Dokument vollstaendig geloescht (DSGVO).")
                        else:
                            st.error("Loeschung fehlgeschlagen.")
                        st.session_state.pop(f"confirm_delete_{doc['id']}", None)
                        st.rerun()
                    else:
                        st.session_state[f"confirm_delete_{doc['id']}"] = True
                        st.warning("Nochmal klicken zum Bestaetigen!")

            # Show details if requested
            if st.session_state.get(f"show_details_{doc['id']}", False):
                with st.expander("Details", expanded=True):
                    st.json({
                        "ID": doc['id'],
                        "Dateiname": doc['filename'],
                        "Typ": doc.get('file_type', 'N/A'),
                        "Status": doc['status'],
                        "Hochgeladen": doc['uploaded_at'],
                        "Letzte Aenderung": doc.get('last_modified', 'N/A'),
                        "Chunks": doc.get('chunk_count', 0),
                        "PII erkannt": "Ja" if doc['pii_detected'] else "Nein",
                        "PII-Zusammenfassung": doc.get('pii_summary', 'Keine')
                    })
                    if st.button("Schliessen", key=f"close_{doc['id']}"):
                        st.session_state[f"show_details_{doc['id']}"] = False
                        st.rerun()
    elif backend_ok:
        st.info("Keine Dokumente gefunden.")
    else:
        st.warning("Backend nicht erreichbar.")


# ============== FOOTER ==============

st.markdown("---")
st.markdown(
    f'<div style="text-align: center; color: #475569; font-size: 16px;">'
    f'SentinelAI Box &bull; 100% Lokal &amp; DSGVO-konform &bull; '
    f'Stand: {datetime.now().strftime("%d.%m.%Y %H:%M")}'
    f'</div>',
    unsafe_allow_html=True
)
