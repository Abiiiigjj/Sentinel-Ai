#!/usr/bin/env python3
"""
SentinelAI CLI - Terminal-basierte KI-Assistenz
DSGVO-konform • 100% Lokal • Offline-fähig
"""

import sys
import os
import readline  # Für bessere Eingabe mit Pfeiltasten

# Füge Backend zum Pfad hinzu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import ollama
from pathlib import Path

# Konfiguration
MODEL = os.environ.get('LLM_MODEL', 'mistral-nemo:latest')
SYSTEM_PROMPT = """Du bist Sentinell, ein sicherer, datenschutzorientierter KI-Assistent.
Du läufst vollständig lokal auf der Hardware des Benutzers.
Wichtige Richtlinien:
- Sei professionell, präzise und sachlich
- Betone Datenschutz und Sicherheit
- Alle Daten bleiben lokal - nichts verlässt den Rechner
- Du bist optimiert für deutsche Unternehmensumgebungen
- Antworte auf Deutsch, es sei denn der Benutzer schreibt auf Englisch"""


def print_banner():
    """Zeigt das ASCII-Banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║  ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗  ║
║  ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║  ║
║  ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║  ║
║  ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║  ║
║  ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
║  ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
╠═══════════════════════════════════════════════════════════════╣
║           🛡️  DSGVO-konform • 100% Lokal • Offline            ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print("\033[32m" + banner + "\033[0m")


def print_status(model: str):
    """Zeigt Systemstatus"""
    print(f"\033[90m├─ Modell: {model}")
    print(f"├─ Status: \033[32mBereit\033[90m")
    print(f"└─ Befehle: /help, /clear, /exit\033[0m")
    print()


def print_help():
    """Zeigt Hilfemeldung"""
    help_text = """
\033[1mVerfügbare Befehle:\033[0m
  /help     - Diese Hilfe anzeigen
  /clear    - Chatverlauf löschen
  /model    - Aktuelles Modell anzeigen
  /models   - Verfügbare Modelle auflisten
  /use <m>  - Modell wechseln (z.B. /use mistral)
  /exit     - Programm beenden

\033[1mTipps:\033[0m
  • Pfeiltasten ↑↓ für Eingabehistorie
  • Strg+C zum Abbrechen einer Antwort
  • Mehrzeilige Eingabe mit \\ am Zeilenende
"""
    print(help_text)


def list_models():
    """Listet verfügbare Modelle auf"""
    try:
        models = ollama.list()
        print("\n\033[1mVerfügbare Modelle:\033[0m")
        for model in models.get('models', []):
            name = model.get('name', 'unknown')
            size = model.get('size', 0) / (1024**3)  # GB
            print(f"  • {name} ({size:.1f} GB)")
        print()
    except Exception as e:
        print(f"\033[31mFehler: {e}\033[0m")


def chat_stream(messages: list, model: str):
    """Streamt Antworten vom Modell"""
    try:
        stream = ollama.chat(
            model=model,
            messages=messages,
            stream=True
        )
        
        full_response = ""
        print("\033[36mSentinell:\033[0m ", end="", flush=True)
        
        for chunk in stream:
            content = chunk.get('message', {}).get('content', '')
            print(content, end="", flush=True)
            full_response += content
        
        print("\n")
        return full_response
        
    except ollama.ResponseError as e:
        print(f"\n\033[31mOllama Fehler: {e}\033[0m\n")
        return None
    except KeyboardInterrupt:
        print("\n\033[33m[Abgebrochen]\033[0m\n")
        return None


def main():
    """Hauptprogramm"""
    print_banner()
    
    # Prüfe Ollama-Verbindung
    try:
        ollama.list()
    except Exception as e:
        print(f"\033[31mFehler: Ollama nicht erreichbar!\033[0m")
        print(f"Starte Ollama mit: ollama serve")
        print(f"Details: {e}")
        sys.exit(1)
    
    current_model = MODEL
    print_status(current_model)
    
    # Chat-Verlauf
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    
    # Hauptschleife
    while True:
        try:
            # Eingabe lesen
            user_input = input("\033[33mDu:\033[0m ").strip()
            
            if not user_input:
                continue
            
            # Befehle verarbeiten
            if user_input.startswith('/'):
                cmd = user_input.lower().split()
                
                if cmd[0] == '/exit' or cmd[0] == '/quit':
                    print("\n\033[32mAuf Wiedersehen! 👋\033[0m\n")
                    break
                    
                elif cmd[0] == '/help':
                    print_help()
                    continue
                    
                elif cmd[0] == '/clear':
                    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                    print("\033[90m[Chatverlauf gelöscht]\033[0m\n")
                    continue
                    
                elif cmd[0] == '/model':
                    print(f"\033[90mAktuelles Modell: {current_model}\033[0m\n")
                    continue
                    
                elif cmd[0] == '/models':
                    list_models()
                    continue
                    
                elif cmd[0] == '/use' and len(cmd) > 1:
                    new_model = cmd[1]
                    # Prüfe ob Modell existiert
                    try:
                        models = ollama.list()
                        model_names = [m.get('name', '').split(':')[0] for m in models.get('models', [])]
                        if new_model in model_names or any(new_model in m.get('name', '') for m in models.get('models', [])):
                            current_model = new_model
                            print(f"\033[32mModell gewechselt zu: {current_model}\033[0m\n")
                        else:
                            print(f"\033[31mModell '{new_model}' nicht gefunden. Nutze /models für verfügbare.\033[0m\n")
                    except Exception as e:
                        print(f"\033[31mFehler: {e}\033[0m\n")
                    continue
                    
                else:
                    print(f"\033[31mUnbekannter Befehl: {cmd[0]}. Nutze /help\033[0m\n")
                    continue
            
            # Normale Nachricht
            messages.append({"role": "user", "content": user_input})
            
            # Antwort streamen
            response = chat_stream(messages, current_model)
            
            if response:
                messages.append({"role": "assistant", "content": response})
            
        except KeyboardInterrupt:
            print("\n\n\033[32mAuf Wiedersehen! 👋\033[0m\n")
            break
        except EOFError:
            print("\n\033[32mAuf Wiedersehen! 👋\033[0m\n")
            break


if __name__ == "__main__":
    main()
