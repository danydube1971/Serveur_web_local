import PySimpleGUI as sg
import threading
import socket
import queue
import sys
import io
import webbrowser
from flask import Flask, send_from_directory, render_template
import os

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

@app.route('/')
def list_files():
    if folder_to_share is None:
        return "Aucun dossier sélectionné."
    else:
        all_items = os.listdir(folder_to_share)
        visible_items = [item for item in all_items if not item.startswith('.')]

        # Dossiers
        folders = sorted([item for item in visible_items if os.path.isdir(os.path.join(folder_to_share, item))])

        # Fichiers avec taille, triés alphabétiquement
        files_with_size = []
        for item in sorted(visible_items):
            if os.path.isfile(os.path.join(folder_to_share, item)):
                size_bytes = os.path.getsize(os.path.join(folder_to_share, item))
                size_megabytes = round(size_bytes / (1024 * 1024), 2)  # Taille en mégaoctets, arrondie à deux décimales
                files_with_size.append((item, size_megabytes))
        
        return render_template('list_files.html', folders=folders, files=files_with_size)



@app.route('/download/<path:filename>')
def download_file(filename):
    print(f"Fichier demandé pour téléchargement: {filename}")
    return send_from_directory(folder_to_share, filename)


def start_flask_app(folder_path):
    global folder_to_share
    folder_to_share = folder_path
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)

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

# Adresse IP locale et port
local_ip = get_local_ip()
flask_port = "5000"
flask_address = f"http://{local_ip}:{flask_port}"

# Redirection de la sortie standard
output_queue = queue.Queue()
sys.stdout = StreamRedirection(output_queue)

# Layout PySimpleGUI
layout = [
    [sg.Text("Choisissez un dossier à partager:")],
    [sg.Input(key='-FOLDER-'), sg.FolderBrowse('Parcourir')],
    [sg.Button('Démarrer le Serveur'), sg.Button('Quitter')],
    [sg.Text('Adresse du Serveur:'), sg.InputText(flask_address, key='-SERVER-ADDRESS-', readonly=True), sg.Button('Ouvrir la page du serveur')],
    [sg.Text("État du serveur et logs :")],
    [sg.Multiline(key='-SERVER-LOG-', size=(60, 15), disabled=True)]
]

# Créer la fenêtre
window = sg.Window('Serveur de Fichiers Flask', layout)

# Fonction pour mettre à jour la boîte de texte avec les logs
def update_output():
    while True:
        try:
            message = output_queue.get(block=False)
        except queue.Empty:
            break
        else:
            window['-SERVER-LOG-'].update(message, append=True)

# Boucle de l'interface graphique
while True:
    event, values = window.read(timeout=100)
    if event in (sg.WIN_CLOSED, 'Quitter'):
        break
    elif event == 'Démarrer le Serveur':
        folder_path = values['-FOLDER-']
        if folder_path:
            flask_thread = threading.Thread(target=start_flask_app, args=(folder_path,), daemon=True)
            flask_thread.start()
            window['-SERVER-ADDRESS-'].update(flask_address)
    elif event == 'Ouvrir la page du serveur':
        webbrowser.open(flask_address)
    update_output()

window.close()

# Restaurer la sortie standard à la normale
sys.stdout = sys.__stdout__

# Pour créer un fichier exécutable avec toutes les dépendances et le dossier "templates" :
# pyinstaller --onefile --add-data 'templates:templates' Serveur_fichiers_local_GUI.py


