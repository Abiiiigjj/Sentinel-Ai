"""
SentinelAI Box - Professional Kiosk Frontend
100% Deutsch | Touchscreen-optimiert | Für Kleinunternehmer
"""
import streamlit as st
import sys
import os
from pathlib import Path
from datetime import datetime, date
import requests

# Add backend to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from services.database_service import DatabaseService

# ============== CONFIG ==============
API_BASE = os.getenv("API_BASE", "http://backend:8000")

st.set_page_config(
    page_title="SentinelAI Box",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"  # Kiosk mode: sidebar nur für Status
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
        font-size: 18px !important;  /* Größere Basisschrift */
    }
    
    /* Große Buttons für Touchscreen */
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
    
    /* Tabs größer */
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
    
    /* Sidebar (nur Status anzeigen) */
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


# ============== INIT DATABASE ==============
@st.cache_resource
def get_database():
    """Initialize database service (singleton)."""
    db_path = backend_path.parent.parent / "data" / "sentinel.db"
    return DatabaseService(db_path=str(db_path))

db = get_database()


# ============== HELPER FUNCTIONS ==============

def check_backend_health() -> dict:
    """Check if backend is online."""
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=2)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return {"status": "offline", "ollama_connected": False}


def format_status_badge(status: str) -> str:
    """Return HTML badge for document status."""
    status_map = {
        "Neu": "status-badge-neu",
        "In Prüfung": "status-badge-pruefung",
        "Erledigt": "status-badge-erledigt",
        "Archiviert": "status-badge-erledigt"
    }
    css_class = status_map.get(status, "status-badge-neu")
    return f'<span class="{css_class}">{status}</span>'


# ============== SIDEBAR: SYSTEM STATUS ==============

with st.sidebar:
    st.markdown("## 🛡️ System")
    st.markdown("---")
    
    health = check_backend_health()
    backend_ok = health.get("status") != "offline"
    ollama_ok = health.get("ollama_connected", False)
    
    if backend_ok:
        st.markdown("🟢 **Backend Online**")
    else:
        st.markdown("🔴 **Backend Offline**")
    
    if ollama_ok:
        st.markdown("🟢 **KI Bereit**")
    else:
        st.markdown("🟠 **KI Nicht verfügbar**")
    
    # DB Stats
    stats = db.get_statistics()
    st.markdown("---")
    st.markdown("### 📊 Datenbank")
    st.metric("Dokumente", stats.get("total_documents", 0))
    st.metric("PII-Fälle", stats.get("pii_documents", 0))
    st.metric("Audit-Einträge", stats.get("audit_entries", 0))
    
    if st.button("🔄 Aktualisieren"):
        st.rerun()


# ============== HEADER ==============

st.markdown("""
<div class="main-header">
    <h1>🛡️ SentinelAI Box</h1>
    <p>Dokumenten-Management mit KI • 100% Lokal & DSGVO-konform</p>
</div>
""", unsafe_allow_html=True)


# ============== TABS ==============

tab_cockpit, tab_posteingang, tab_archiv = st.tabs([
    "📊 Cockpit",
    "📥 Posteingang", 
    "🗄️ Archiv"
])


# ==================== TAB A: COCKPIT ====================

with tab_cockpit:
    st.markdown("## 📊 Übersicht")
    
    # Metriken
    stats = db.get_statistics()
    status_counts = stats.get("status_counts", {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📋 Offene Dokumente",
            value=status_counts.get("Neu", 0),
            help="Dokumente mit Status 'Neu'"
        )
    
    with col2:
        st.metric(
            label="🔍 In Prüfung",
            value=status_counts.get("In Prüfung", 0),
            help="Dokumente werden geprüft"
        )
    
    with col3:
        st.metric(
            label="✅ Erledigt",
            value=status_counts.get("Erledigt", 0),
            help="Abgeschlossene Dokumente"
        )
    
    with col4:
        st.metric(
            label="⚠️ PII-Fälle",
            value=stats.get("pii_documents", 0),
            help="Dokumente mit personenbezogenen Daten"
        )
    
    st.markdown("---")
    
    # Recent documents
    st.markdown("### 📄 Aktuelle Dokumente")
    
    recent_docs = db.get_all_documents(limit=10)
    
    if recent_docs:
        for doc in recent_docs:
            doc_id = doc["id"]
            filename = doc["filename"]
            status = doc["status"]
            uploaded = doc["uploaded_at"]
            pii = doc["pii_detected"]
            
            # Parse timestamp
            try:
                dt = datetime.fromisoformat(uploaded)
                time_str = dt.strftime("%d.%m.%Y %H:%M")
            except:
                time_str = uploaded
            
            with st.container():
                st.markdown(f"""
                <div class="doc-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="font-size: 18px;">📄 {filename}</strong><br>
                            <small style="color: #94a3b8;">Hochgeladen: {time_str}</small>
                        </div>
                        <div style="text-align: right;">
                            {format_status_badge(status)}
                            {'<span style="margin-left: 12px;">⚠️ PII</span>' if pii else ''}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Inline status change
                col_a, col_b, col_c, col_d = st.columns([1, 1, 1, 3])
                with col_a:
                    if st.button("▶️ Prüfung", key=f"pruef_{doc_id}"):
                        db.update_document_status(doc_id, "In Prüfung")
                        db.add_audit_log("status_change", metadata=f"Status → In Prüfung", document_id=doc_id)
                        st.rerun()
                with col_b:
                    if st.button("✅ Erledigt", key=f"done_{doc_id}"):
                        db.update_document_status(doc_id, "Erledigt")
                        db.add_audit_log("status_change", metadata=f"Status → Erledigt", document_id=doc_id)
                        st.rerun()
                with col_c:
                    if st.button("🗑️ Archiv", key=f"arch_{doc_id}"):
                        db.archive_document(doc_id)
                        db.add_audit_log("document_archived", document_id=doc_id)
                        st.rerun()
    else:
        st.info("📭 Noch keine Dokumente vorhanden. Nutze den Posteingang zum Hochladen.")


# ==================== TAB B: POSTEINGANG ====================

with tab_posteingang:
    st.markdown("## 📥 Posteingang")
    st.markdown("Dokumente hochladen und automatisch analysieren lassen.")
    
    uploaded_file = st.file_uploader(
        "Dokument auswählen",
        type=["pdf", "txt", "docx", "doc"],
        help="Unterstützte Formate: PDF, TXT, DOCX (max. 50MB)",
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        st.markdown(f"""
        <div class="doc-card">
            <strong>📎 {uploaded_file.name}</strong><br>
            <small>Größe: {uploaded_file.size / 1024:.1f} KB</small>
        </div>
        """, unsafe_allow_html=True)
        
        col_up1, col_up2 = st.columns([1, 3])
        with col_up1:
            upload_btn = st.button("📤 Hochladen & Analysieren", type="primary", use_container_width=True)
        
        if upload_btn:
            if not backend_ok:
                st.error("❌ Backend ist offline. Starte das Backend mit: `python src/backend/main.py`")
            else:
                with st.spinner("🔄 Dokument wird verarbeitet..."):
                    try:
                        # Upload to backend
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        resp = requests.post(f"{API_BASE}/documents/upload", files=files, timeout=300)
                        
                        # Better error handling with status code and response body
                        if resp.status_code != 200:
                            st.error(f"❌ Upload fehlgeschlagen (HTTP {resp.status_code})")
                            with st.expander("🔍 Technische Details (für Support)"):
                                st.code(f"""REQUEST URL: {API_BASE}/documents/upload
HTTP METHOD: POST
HTTP STATUS: {resp.status_code}

RESPONSE HEADERS:
{dict(resp.headers)}

RESPONSE BODY:
{resp.text}
                                """, language="text")
                            st.stop()
                        
                        result = resp.json()
                        
                        doc_id = result.get("id")
                        chunks = result.get("chunk_count", 0)
                        pii_detected = result.get("pii_detected", False)
                        pii_summary = result.get("pii_summary", "")
                        
                        # Save to database
                        db.add_document(
                            doc_id=doc_id,
                            filename=uploaded_file.name,
                            file_size=uploaded_file.size,
                            file_type=uploaded_file.name.split(".")[-1],
                            chunk_count=chunks,
                            pii_detected=pii_detected,
                            pii_summary=pii_summary
                        )
                        
                        # Audit log
                        db.add_audit_log(
                            action="document_upload",
                            document_id=doc_id,
                            metadata=f"Uploaded: {uploaded_file.name}, Chunks: {chunks}, PII: {pii_detected}"
                        )
                        
                        st.markdown("""
                        <div class="success-box">
                            ✅ <strong>Dokument erfolgreich verarbeitet!</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_m1, col_m2, col_m3 = st.columns(3)
                        with col_m1:
                            st.metric("Dokument-ID", doc_id[:8] + "...")
                        with col_m2:
                            st.metric("Text-Abschnitte", chunks)
                        with col_m3:
                            st.metric("PII erkannt", "⚠️ Ja" if pii_detected else "✅ Nein")
                        
                        if pii_detected:
                            st.markdown(f"""
                            <div class="pii-warning">
                                <strong>⚠️ Personenbezogene Daten erkannt:</strong><br>
                                {pii_summary or 'Details nicht verfügbar'}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("---")
                        st.markdown("### ⚡ Schnellaktionen")
                        
                        col_a1, col_a2, col_a3 = st.columns(3)
                        with col_a1:
                            if st.button("✅ Akzeptieren & Erledigen", use_container_width=True):
                                db.update_document_status(doc_id, "Erledigt")
                                db.add_audit_log("quick_accept", document_id=doc_id)
                                st.success("Dokument als erledigt markiert!")
                                st.rerun()
                        with col_a2:
                            if st.button("🔍 Zur Prüfung", use_container_width=True):
                                db.update_document_status(doc_id, "In Prüfung")
                                db.add_audit_log("mark_review", document_id=doc_id)
                                st.success("Zur Prüfung markiert!")
                                st.rerun()
                        with col_a3:
                            if st.button("🗑️ Archivieren", use_container_width=True):
                                db.archive_document(doc_id)
                                db.add_audit_log("quick_archive", document_id=doc_id)
                                st.success("Archiviert!")
                                st.rerun()
                        
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Verbindung zum Backend fehlgeschlagen.")
                        st.info("💡 Stelle sicher, dass das Backend läuft: `docker ps | grep sentinelai-backend`")
                    except requests.exceptions.Timeout:
                        st.error("❌ Request-Timeout. Dokument zu groß oder Backend überlastet.")
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Request-Fehler: {type(e).__name__}")
                        if hasattr(e, 'response') and e.response is not None:
                            with st.expander("🔍 Technische Details"):
                                st.code(f"Status: {e.response.status_code}\n\n{e.response.text}", language="text")
                    except Exception as e:
                        st.error(f"❌ Unerwarteter Fehler: {e}")
    
    st.markdown("---")
    st.markdown("### 📊 Offene Dokumente (Status: Neu)")
    
    new_docs = db.get_all_documents(status="Neu", limit=20)
    
    if new_docs:
        for doc in new_docs:
            with st.expander(f"📄 {doc['filename']} — {format_status_badge(doc['status'])}", expanded=False):
                st.write(f"**Hochgeladen:** {doc['uploaded_at']}")
                st.write(f"**PII erkannt:** {'⚠️ Ja' if doc['pii_detected'] else '✅ Nein'}")
                if doc['pii_summary']:
                    st.warning(f"PII: {doc['pii_summary']}")
                
                col_x1, col_x2 = st.columns(2)
                with col_x1:
                    if st.button("✅ Erledigen", key=f"finish_{doc['id']}"):
                        db.update_document_status(doc['id'], "Erledigt")
                        db.add_audit_log("mark_done", document_id=doc['id'])
                        st.rerun()
                with col_x2:
                    if st.button("🗑️ Löschen (DSGVO)", key=f"del_{doc['id']}"):
                        db.delete_document(doc['id'])
                        db.add_audit_log("gdpr_deletion", document_id=doc['id'])
                        st.rerun()
    else:
        st.info("✅ Keine offenen Dokumente.")


# ==================== TAB C: ARCHIV ====================

with tab_archiv:
    st.markdown("## 🗄️ Archiv & Suche")
    
    # Search section
    st.markdown("### 🔍 Semantische Suche")
    
    search_query = st.text_input(
        "Suche in allen Dokumenten:",
        placeholder="z.B. 'Vertragsbedingungen' oder 'Datenschutz'",
        label_visibility="collapsed"
    )
    
    col_search1, col_search2 = st.columns([1, 4])
    with col_search1:
        search_k = st.number_input("Ergebnisse", 1, 20, 5, label_visibility="collapsed")
    with col_search2:
        search_btn = st.button("🔎 Suchen", type="primary", use_container_width=True)
    
    if search_btn and search_query.strip():
        if not backend_ok:
            st.error("❌ Backend offline. Semantische Suche nicht verfügbar.")
        else:
            with st.spinner("🔄 Suche läuft..."):
                try:
                    resp = requests.get(f"{API_BASE}/api/search/quality", params={
                        "query": search_query,
                        "k": search_k
                    }, timeout=60)
                    resp.raise_for_status()
                    result = resp.json()
                    
                    results_list = result.get("results", [])
                    
                    if results_list:
                        st.success(f"✅ {len(results_list)} Ergebnisse gefunden")
                        
                        for i, res in enumerate(results_list, 1):
                            distance = res.get("distance", 1.0)
                            similarity = max(0, min(1, 1.0 - distance))
                            content = res.get("content", "")[:400]
                            metadata = res.get("metadata", {})
                            filename = metadata.get("filename", "Unbekannt")
                            
                            with st.expander(f"**#{i}** {filename} — Relevanz: {similarity:.0%}"):
                                st.markdown(content)
                                st.caption(f"Dokument-ID: {metadata.get('document_id', 'N/A')[:8]}...")
                    else:
                        st.info("🔍 Keine Ergebnisse gefunden.")
                
                except Exception as e:
                    st.error(f"❌ Suche fehlgeschlagen: {e}")
    
    st.markdown("---")
    st.markdown("### 📁 Filter nach Status")
    
    col_filter1, col_filter2 = st.columns([1, 3])
    with col_filter1:
        filter_status = st.selectbox(
            "Status:",
            ["Alle", "Neu", "In Prüfung", "Erledigt"],
            label_visibility="collapsed"
        )
    
    status_filter = None if filter_status == "Alle" else filter_status
    filtered_docs = db.get_all_documents(status=status_filter, limit=50)
    
    st.markdown(f"**{len(filtered_docs)} Dokument(e) gefunden**")
    
    if filtered_docs:
        for doc in filtered_docs:
            with st.container():
                st.markdown(f"""
                <div class="doc-card">
                    <strong style="font-size: 18px;">📄 {doc['filename']}</strong> — {format_status_badge(doc['status'])}<br>
                    <small style="color: #94a3b8;">
                        Hochgeladen: {doc['uploaded_at']} | 
                        {'⚠️ PII erkannt' if doc['pii_detected'] else '✅ Keine PII'}
                    </small>
                </div>
                """, unsafe_allow_html=True)
                
                col_z1, col_z2, col_z3 = st.columns([1, 1, 3])
                with col_z1:
                    if st.button("📝 Details", key=f"details_{doc['id']}"):
                        st.session_state[f"show_details_{doc['id']}"] = True
                        st.rerun()
                with col_z2:
                    if st.button("🗑️ Löschen", key=f"delete_{doc['id']}"):
                        if st.session_state.get(f"confirm_delete_{doc['id']}", False):
                            db.delete_document(doc['id'])
                            db.add_audit_log("delete_from_archive", document_id=doc['id'])
                            st.success("Gelöscht!")
                            st.rerun()
                        else:
                            st.session_state[f"confirm_delete_{doc['id']}"] = True
                            st.warning("Nochmal klicken zum Bestätigen!")
                
                # Show details if requested
                if st.session_state.get(f"show_details_{doc['id']}", False):
                    with st.expander("📋 Details", expanded=True):
                        st.json({
                            "ID": doc['id'],
                            "Dateiname": doc['filename'],
                            "Größe": f"{doc.get('file_size', 0) / 1024:.1f} KB",
                            "Typ": doc.get('file_type', 'N/A'),
                            "Status": doc['status'],
                            "Hochgeladen": doc['uploaded_at'],
                            "Letzte Änderung": doc.get('last_modified', 'N/A'),
                            "Chunks": doc.get('chunk_count', 0),
                            "PII erkannt": "Ja" if doc['pii_detected'] else "Nein",
                            "PII-Zusammenfassung": doc.get('pii_summary', 'Keine')
                        })
                        if st.button("Schließen", key=f"close_{doc['id']}"):
                            st.session_state[f"show_details_{doc['id']}"] = False
                            st.rerun()
    else:
        st.info("Keine Dokumente gefunden.")


# ============== FOOTER ==============

st.markdown("---")
st.markdown(
    f'<div style="text-align: center; color: #475569; font-size: 16px;">'
    f'🛡️ SentinelAI Box • 100% Lokal & DSGVO-konform • '
    f'Stand: {datetime.now().strftime("%d.%m.%Y %H:%M")}'
    f'</div>',
    unsafe_allow_html=True
)
