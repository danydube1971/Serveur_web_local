import sys
import io
import socket
import threading
import queue
import os
import webbrowser
from datetime import datetime
from werkzeug.serving import make_server
from pathlib import Path
import subprocess
import time

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QTextEdit, QVBoxLayout, QHBoxLayout, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor
from flask import Flask, send_from_directory, render_template, send_file, request, abort, Response

# Liste de ports souvent bloqués par les navigateurs (non sécurisés)
UNSAFE_PORTS = {6000, 6001, 6002, 6003, 6004, 6005, 6006, 6007, 6063}

# Classe personnalisée pour rediriger la sortie standard
class StreamRedirection(io.StringIO):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    def write(self, text):
        super().write(text)
        self.queue.put(text)

# Application Flask
if getattr(sys, 'frozen', False):
    template_dir = os.path.join(sys._MEIPASS, 'templates')
    app = Flask(__name__, template_folder=template_dir)
else:
    app = Flask(__name__)

folder_to_share = None
folder_to_share_realpath = None  # Chemin réel calculé une fois
flask_server = None

# Cache pour les listings de fichiers (chemin -> (résultat, timestamp))
listing_cache = {}
CACHE_TTL = 60  # Durée de vie du cache en secondes (60s)

# Liste blanche des extensions autorisées (globale, modifiable)
ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.jpg', '.png', '.mp3', '.mp4', '.mkv', '.odt', '.wav'}

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_index_or_list(path):
    global folder_to_share, folder_to_share_realpath, listing_cache
    if folder_to_share is None or folder_to_share_realpath is None:
        return "Serveur arrêté ou aucun dossier sélectionné."

    requested_path = os.path.join(folder_to_share, path)
    requested_path_real = os.path.realpath(requested_path)
    # Normalisation pour éviter les problèmes de casse ou de séparateurs
    folder_to_share_norm = os.path.normpath(folder_to_share_realpath)
    requested_path_norm = os.path.normpath(requested_path_real)
    if not requested_path_norm.startswith(folder_to_share_norm):
        print(f"Accès refusé : {requested_path_norm} ne commence pas par {folder_to_share_norm}")
        abort(403)

    if os.path.isfile(requested_path):
        return send_file(requested_path)

    if path == "favicon.ico":
        return Response("", mimetype="image/x-icon")

    index_path = os.path.join(requested_path, 'index.html')
    if os.path.isfile(index_path):
        client_ip = request.remote_addr
        now = datetime.now()
        timestamp = now.strftime("%d-%b-%y %H:%M:%S").upper()
        print(f"Page index.html affichée pour {client_ip} à {timestamp}")
        return send_file(index_path)

    if not os.path.isdir(requested_path):
        abort(404)

    # Vérifier le cache
    current_time = time.time()
    cache_key = requested_path
    if cache_key in listing_cache:
        cached_result, cache_time = listing_cache[cache_key]
        if current_time - cache_time < CACHE_TTL:
            print(f"Utilisation du cache pour le chemin : {cache_key}")
            return cached_result

    # Générer la liste des fichiers si pas dans le cache ou TTL expiré
    all_items = os.listdir(requested_path)
    visible_items = [item for item in all_items if not item.startswith('.')]

    folders = sorted([item for item in visible_items if os.path.isdir(os.path.join(requested_path, item))])
    files_with_size = []
    for item in sorted(visible_items):
        if os.path.isfile(os.path.join(requested_path, item)):
            # Filtrer selon les extensions autorisées
            if Path(item).suffix.lower() in ALLOWED_EXTENSIONS:
                size_bytes = os.path.getsize(os.path.join(requested_path, item))
                size_megabytes = round(size_bytes / (1024 * 1024), 2)
                files_with_size.append((item, size_megabytes))

    parent_path = os.path.dirname(path) if path else None
    result = render_template('list_files.html', folders=folders, files=files_with_size, current_path=path, parent_path=parent_path)

    # Mettre à jour le cache
    listing_cache[cache_key] = (result, current_time)
    print(f"Mise en cache du chemin : {cache_key}")

    return result

@app.route('/download/<path:filename>')
def serve_file(filename):
    global folder_to_share, folder_to_share_realpath
    if folder_to_share is None or folder_to_share_realpath is None:
        return "Serveur arrêté ou aucun dossier sélectionné."

    full_path = os.path.join(folder_to_share, filename)
    full_path_real = os.path.realpath(full_path)
    # Normalisation pour éviter les problèmes de casse ou de séparateurs
    folder_to_share_norm = os.path.normpath(folder_to_share_realpath)
    full_path_norm = os.path.normpath(full_path_real)
    if not full_path_norm.startswith(folder_to_share_norm):
        print(f"Accès refusé : {full_path_norm} ne commence pas par {folder_to_share_norm}")
        abort(403)

    if not os.path.exists(full_path):
        abort(404)

    # Vérification de l'extension du fichier
    if Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        print(f"Accès refusé : l'extension de '{filename}' n'est pas autorisée.")
        abort(403)

    # Log uniquement si ce n'est pas une requête Range (code 206)
    if 'Range' not in request.headers:
        client_ip = request.remote_addr
        now = datetime.now()
        timestamp = now.strftime("%d-%b-%y %H:%M:%S").upper()
        print(f"Fichier téléchargé: '{filename}' par {client_ip} à {timestamp}")
    
    return send_from_directory(folder_to_share, filename)

def start_flask_app(folder_path, port, log_queue):
    global folder_to_share, folder_to_share_realpath, flask_server
    folder_to_share = folder_path
    folder_to_share_realpath = os.path.realpath(folder_to_share)
    log_queue.put(f"Chemin réel calculé : {folder_to_share_realpath}")
    # Vérification supplémentaire
    if not os.path.exists(folder_to_share_realpath):
        log_queue.put(f"Erreur : Le dossier {folder_to_share_realpath} n'existe pas ou n'est pas accessible")
    try:
        flask_server = make_server('0.0.0.0', port, app, threaded=True)
        flask_server.serve_forever()
    except OSError as e:
        log_queue.put(f"Erreur: Impossible de démarrer le serveur sur le port {port} - {str(e)}")
        flask_server = None

def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            return ip
    except Exception as e:
        print(f"Erreur lors de l'obtention de l'adresse IP locale : {e}")
        return "Inconnu"

def check_port_open(ip, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            return sock.connect_ex((ip, port)) == 0
    except Exception as e:
        print(f"Erreur lors de la vérification du port : {e}")
        return False

def check_port_available(port):
    """Vérifie si le port peut être lié (disponible pour le serveur)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('0.0.0.0', port))
            return True
    except OSError as e:
        return False

def get_process_using_port(port):
    try:
        result = subprocess.run(['ss', '-tln', '-p', f'sport = :{port}'], capture_output=True, text=True)
        output = result.stdout.strip()
        if output:
            for line in output.splitlines()[1:]:
                if f":{port}" in line:
                    parts = line.split()
                    if "users:" in line:
                        users_part = line.split("users:")[1].strip("()")
                        process_info = users_part.split(",")
                        process_name = process_info[0].strip('"')
                        pid = process_info[1].split("=")[1]
                        return f"{process_name} (PID: {pid})"
        return "Inconnu (aucun processus en écoute identifiable)"
    except Exception as e:
        print(f"Erreur lors de la vérification du processus : {str(e)}")
        return "Inconnu (erreur lors de la vérification)"

class FileServerGUI(QWidget):
    def __init__(self, local_ip):
        super().__init__()
        self.setWindowTitle("Serveur de Fichiers Flask")
        self.setGeometry(100, 100, 700, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: #2E2E2E;
                color: #FFFFFF;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit {
                background-color: #3C3C3C;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #4A90E2;
                border: none;
                border-radius: 5px;
                padding: 8px;
                color: #FFFFFF;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
            QPushButton:pressed {
                background-color: #2A5D99;
            }
            QTextEdit {
                background-color: #3C3C3C;
                border: 1px solid #555555;
                border-radius: 5px;
                color: #FFFFFF;
            }
            QLabel {
                color: #D0D0D0;
            }
            QFrame#sectionFrame {
                background-color: #363636;
                border-radius: 10px;
                padding: 10px;
            }
        """)

        self.local_ip = local_ip  # Utiliser l'IP passée en paramètre
        self.default_port = "8080"  # Port par défaut à 8080
        self.flask_port = self.default_port
        self.flask_address = f"http://{self.local_ip}:{self.flask_port}"
        self.server_running = False
        self.flask_thread = None

        # Limite à 1000 éléments pour éviter saturation mémoire
        self.output_queue = queue.Queue(maxsize=1000)
        sys.stdout = StreamRedirection(self.output_queue)

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Section supérieure (dossier et port)
        top_frame = QFrame()
        top_frame.setObjectName("sectionFrame")
        top_layout = QVBoxLayout(top_frame)

        folder_layout = QHBoxLayout()
        self.folder_label = QLabel("Choisissez un dossier à partager:")
        self.folder_label.setFont(QFont("Segoe UI", 10))
        self.folder_input = QLineEdit()
        self.folder_input.setFont(QFont("Segoe UI", 10))
        self.browse_button = QPushButton("Parcourir")
        self.browse_button.setFont(QFont("Segoe UI", 10))
        self.browse_button.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(self.browse_button)
        top_layout.addLayout(folder_layout)

        port_layout = QHBoxLayout()
        self.port_label = QLabel("Port réseau:")
        self.port_label.setFont(QFont("Segoe UI", 10))
        self.port_input = QLineEdit(self.default_port)
        self.port_input.setFont(QFont("Segoe UI", 10))
        self.port_input.setMaximumWidth(100)
        port_layout.addWidget(self.port_label)
        port_layout.addWidget(self.port_input)
        port_layout.addStretch()
        top_layout.addLayout(port_layout)

        main_layout.addWidget(top_frame)

        # Section des contrôles
        control_frame = QFrame()
        control_frame.setObjectName("sectionFrame")
        control_layout = QHBoxLayout(control_frame)
        self.start_stop_button = QPushButton("Démarrer le Serveur")
        self.start_stop_button.setFont(QFont("Segoe UI", 10))
        self.start_stop_button.clicked.connect(self.toggle_server)
        self.quit_button = QPushButton("Quitter")
        self.quit_button.setFont(QFont("Segoe UI", 10))
        self.quit_button.clicked.connect(self.close)
        control_layout.addWidget(self.start_stop_button)
        control_layout.addStretch()
        control_layout.addWidget(self.quit_button)
        main_layout.addWidget(control_frame)

        # Section de l'adresse du serveur et extensions autorisées
        server_frame = QFrame()
        server_frame.setObjectName("sectionFrame")
        server_layout = QVBoxLayout(server_frame)  # Changé en VBox pour ajouter les extensions en dessous

        # Adresse du serveur
        address_layout = QHBoxLayout()
        self.server_address_label = QLabel("Adresse du Serveur:")
        self.server_address_label.setFont(QFont("Segoe UI", 10))
        self.server_address_input = QLineEdit(self.flask_address)
        self.server_address_input.setFont(QFont("Segoe UI", 10))
        self.server_address_input.setReadOnly(True)
        self.open_browser_button = QPushButton("Ouvrir la page du serveur")
        self.open_browser_button.setFont(QFont("Segoe UI", 10))
        self.open_browser_button.clicked.connect(self.open_server_page)
        address_layout.addWidget(self.server_address_label)
        address_layout.addWidget(self.server_address_input)
        address_layout.addWidget(self.open_browser_button)
        server_layout.addLayout(address_layout)

        # Extensions autorisées
        extensions_layout = QHBoxLayout()
        self.extensions_label = QLabel("Extensions autorisées:")
        self.extensions_label.setFont(QFont("Segoe UI", 10))
        self.extensions_input = QLineEdit(" ".join(sorted(ALLOWED_EXTENSIONS)))
        self.extensions_input.setFont(QFont("Segoe UI", 10))
        self.extensions_input.textChanged.connect(self.update_allowed_extensions)
        extensions_layout.addWidget(self.extensions_label)
        extensions_layout.addWidget(self.extensions_input)
        server_layout.addLayout(extensions_layout)

        main_layout.addWidget(server_frame)

        # Section des logs
        logs_frame = QFrame()
        logs_frame.setObjectName("sectionFrame")
        logs_layout = QVBoxLayout(logs_frame)
        logs_header_layout = QHBoxLayout()
        logs_label = QLabel("État du serveur et logs:")
        logs_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.clear_logs_button = QPushButton("Effacer les logs")
        self.clear_logs_button.setFont(QFont("Segoe UI", 10))
        self.clear_logs_button.clicked.connect(self.clear_logs)
        logs_header_layout.addWidget(logs_label)
        logs_header_layout.addStretch()
        logs_header_layout.addWidget(self.clear_logs_button)
        
        self.logs_text = QTextEdit()
        self.logs_text.setFont(QFont("Segoe UI", 9))
        self.logs_text.setReadOnly(True)
        logs_layout.addLayout(logs_header_layout)
        logs_layout.addWidget(self.logs_text)
        main_layout.addWidget(logs_frame, stretch=1)

        self.setLayout(main_layout)

        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_logs)
        self.timer.start()

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Sélectionnez un dossier à partager", "")
        if folder:
            self.folder_input.setText(folder)

    def toggle_server(self):
        if not self.server_running:
            self.start_server()
        else:
            self.stop_server()

    def start_server(self):
        folder_path = self.folder_input.text()
        port = self.port_input.text()

        try:
            port = int(port)
            if not (1 <= port <= 65535):
                raise ValueError("Le port doit être compris entre 1 et 65535.")
        except ValueError as e:
            self.logs_text.append(f"Erreur: Port invalide. {str(e)}")
            return

        if port in UNSAFE_PORTS:
            self.logs_text.append(f"Avertissement: Le port {port} est souvent bloqué par les navigateurs (port non sécurisé).")

        if folder_path:
            # Vérification si le port est disponible avant de démarrer
            if not check_port_available(port):
                process_info = get_process_using_port(port)
                self.logs_text.append(f"Erreur: Le port {port} est déjà utilisé par {process_info} ou nécessite des privilèges (ex. root). Choisissez un autre port.")
                return

            self.start_stop_button.setText("Arrêter le Serveur")
            self.port_input.setEnabled(False)
            self.folder_input.setEnabled(False)
            self.extensions_input.setReadOnly(True)  # Verrouiller le champ des extensions
            self.server_running = True
            self.flask_port = str(port)
            self.flask_address = f"http://{self.local_ip}:{self.flask_port}"
            self.server_address_input.setText(self.flask_address)

            # Thread sans daemon=True pour un arrêt contrôlé
            self.flask_thread = threading.Thread(target=start_flask_app, args=(folder_path, port, self.output_queue))
            self.flask_thread.start()

            QTimer.singleShot(1000, self.check_port_status)

            self.logs_text.append(f"Serveur démarré à {self.flask_address}")
        else:
            self.logs_text.append("Veuillez sélectionner un dossier à partager.")

    def stop_server(self):
        global flask_server, folder_to_share_realpath
        if self.server_running and self.flask_thread and flask_server:
            self.start_stop_button.setText("Démarrer le Serveur")
            self.port_input.setEnabled(True)
            self.folder_input.setEnabled(True)
            self.extensions_input.setReadOnly(False)  # Déverrouiller le champ des extensions
            self.server_running = False

            try:
                flask_server.shutdown()
                flask_server.server_close()
                self.flask_thread.join(timeout=5)
                if self.flask_thread.is_alive():
                    self.logs_text.append("Erreur : Le thread du serveur n'a pas pu s'arrêter dans les 5 secondes.")
                else:
                    self.logs_text.append("Serveur arrêté proprement.")
            except Exception as e:
                self.logs_text.append(f"Erreur lors de l'arrêt du serveur : {str(e)}")
            
            self.flask_thread = None
            flask_server = None
            folder_to_share_realpath = None  # Réinitialisation

            QTimer.singleShot(1000, self.check_port_status)

    def update_allowed_extensions(self):
        """Met à jour ALLOWED_EXTENSIONS à partir du champ texte."""
        global ALLOWED_EXTENSIONS
        text = self.extensions_input.text().strip()
        if text:
            # Convertir le texte en ensemble d'extensions (séparées par des espaces)
            new_extensions = set()
            for ext in text.split():
                if ext.startswith('.'):
                    new_extensions.add(ext.lower())
                else:
                    new_extensions.add('.' + ext.lower())
            ALLOWED_EXTENSIONS = new_extensions
            self.logs_text.append(f"Extensions autorisées mises à jour : {' '.join(sorted(ALLOWED_EXTENSIONS))}")
        else:
            self.logs_text.append("Aucune extension spécifiée, liste réinitialisée.")
            ALLOWED_EXTENSIONS = set()

    def check_port_status(self):
        port = int(self.flask_port)
        is_open = check_port_open(self.local_ip, port)
        if is_open:
            process_info = get_process_using_port(port)
            self.logs_text.append(f"Port {port}: Ouvert - Utilisé par {process_info}")
            if port in UNSAFE_PORTS:
                self.logs_text.append(f"Attention: Le port {port} peut être bloqué par certains navigateurs (port non sécurisé).")
        else:
            self.logs_text.append(f"Port {port}: Fermé")

    def open_server_page(self):
        webbrowser.open(self.flask_address)

    def update_logs(self):
        while not self.output_queue.empty():
            message = self.output_queue.get()
            self.logs_text.append(message)

    def clear_logs(self):
        self.logs_text.clear()

    def closeEvent(self, event):
        if self.server_running:
            self.stop_server()
        sys.stdout = sys.__stdout__
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Calculer l'IP locale une seule fois au lancement
    local_ip = get_local_ip()
    
    # Appliquer un thème sombre global
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(46, 46, 46))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(60, 60, 60))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(54, 54, 54))
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(74, 144, 226))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Highlight, QColor(53, 122, 189))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    app.setPalette(palette)

    gui = FileServerGUI(local_ip)  # Passer l'IP calculée à l'instance
    gui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
