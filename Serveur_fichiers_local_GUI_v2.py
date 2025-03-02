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
app = Flask(__name__)
folder_to_share = None
flask_server = None

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_index_or_list(path):
    global folder_to_share
    if folder_to_share is None:
        return "Aucun dossier sélectionné."

    requested_path = os.path.join(folder_to_share, path)
    if not os.path.realpath(requested_path).startswith(os.path.realpath(folder_to_share)):
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

    all_items = os.listdir(requested_path)
    visible_items = [item for item in all_items if not item.startswith('.')]

    folders = sorted([item for item in visible_items if os.path.isdir(os.path.join(requested_path, item))])
    files_with_size = []
    for item in sorted(visible_items):
        if os.path.isfile(os.path.join(requested_path, item)):
            size_bytes = os.path.getsize(os.path.join(requested_path, item))
            size_megabytes = round(size_bytes / (1024 * 1024), 2)
            files_with_size.append((item, size_megabytes))

    parent_path = os.path.dirname(path) if path else None
    return render_template('list_files.html', folders=folders, files=files_with_size, current_path=path, parent_path=parent_path)

@app.route('/download/<path:filename>')
def serve_file(filename):
    global folder_to_share
    full_path = os.path.join(folder_to_share, filename)
    
    if not os.path.realpath(full_path).startswith(os.path.realpath(folder_to_share)):
        abort(403)

    if not os.path.exists(full_path):
        abort(404)

    client_ip = request.remote_addr
    now = datetime.now()
    timestamp = now.strftime("%d-%b-%y %H:%M:%S").upper()
    print(f"Fichier téléchargé: '{filename}' par {client_ip} à {timestamp}")
    
    return send_from_directory(folder_to_share, filename)

def start_flask_app(folder_path, port, log_queue):
    global folder_to_share, flask_server
    folder_to_share = folder_path
    try:
        flask_server = make_server('0.0.0.0', port, app, threaded=True)
        flask_server.serve_forever()
    except OSError as e:
        log_queue.put(f"Erreur: Impossible de démarrer le serveur sur le port {port} - {str(e)}")
        flask_server = None

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"Erreur lors de l'obtention de l'adresse IP locale : {e}")
        return "Inconnu"

def check_port_open(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((ip, port))
    sock.close()
    return result == 0

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
    except subprocess.CalledProcessError as e:
        return f"Erreur lors de la vérification du processus: {str(e)}"

class FileServerGUI(QWidget):
    def __init__(self):
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

        self.local_ip = get_local_ip()
        self.default_port = "5000"
        self.flask_port = self.default_port
        self.flask_address = f"http://{self.local_ip}:{self.flask_port}"
        self.server_running = False
        self.flask_thread = None

        self.output_queue = queue.Queue()
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

        # Section de l'adresse du serveur
        server_frame = QFrame()
        server_frame.setObjectName("sectionFrame")
        server_layout = QHBoxLayout(server_frame)
        self.server_address_label = QLabel("Adresse du Serveur:")
        self.server_address_label.setFont(QFont("Segoe UI", 10))
        self.server_address_input = QLineEdit(self.flask_address)
        self.server_address_input.setFont(QFont("Segoe UI", 10))
        self.server_address_input.setReadOnly(True)
        self.open_browser_button = QPushButton("Ouvrir la page du serveur")
        self.open_browser_button.setFont(QFont("Segoe UI", 10))
        self.open_browser_button.clicked.connect(self.open_server_page)
        server_layout.addWidget(self.server_address_label)
        server_layout.addWidget(self.server_address_input)
        server_layout.addWidget(self.open_browser_button)
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
            if check_port_open(self.local_ip, port):
                process_info = get_process_using_port(port)
                self.logs_text.append(f"Erreur: Le port {port} est déjà utilisé par {process_info}. Choisissez un autre port.")
                return

            self.start_stop_button.setText("Arrêter le Serveur")
            self.port_input.setEnabled(False)
            self.server_running = True
            self.flask_port = str(port)
            self.flask_address = f"http://{self.local_ip}:{self.flask_port}"
            self.server_address_input.setText(self.flask_address)

            self.flask_thread = threading.Thread(target=start_flask_app, args=(folder_path, port, self.output_queue), daemon=True)
            self.flask_thread.start()

            QTimer.singleShot(1000, self.check_port_status)

            self.logs_text.append(f"Serveur démarré à {self.flask_address}")
        else:
            self.logs_text.append("Veuillez sélectionner un dossier à partager.")

    def stop_server(self):
        global flask_server
        if self.server_running and self.flask_thread and flask_server:
            self.start_stop_button.setText("Démarrer le Serveur")
            self.port_input.setEnabled(True)
            self.server_running = False

            flask_server.shutdown()
            self.flask_thread.join(timeout=2)
            if self.flask_thread.is_alive():
                self.logs_text.append("Erreur: Le thread du serveur ne s'est pas arrêté correctement.")
            else:
                self.logs_text.append("Serveur arrêté.")
            self.flask_thread = None
            flask_server = None

            QTimer.singleShot(1000, self.check_port_status)

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

    gui = FileServerGUI()
    gui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
