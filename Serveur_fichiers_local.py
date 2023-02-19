'''Voici un script Python 3 pour Linux Mint qui utilise le module Flask pour lancer un serveur web local et afficher les 
fichiers du dossier courant dans le même emplacement que le script. Les autres utilisateurs du réseau local peuvent accéder 
au serveur en utilisant l'adresse IP 10.0.0.236 et télécharger les fichiers de la page.

Assurez-vous d'installer le module Flask en exécutant la commande suivante dans votre terminal:
pip3 install Flask

Ce script crée un serveur Flask qui affiche une liste de fichiers dans le dossier courant et sous-dossiers en ordre alphabétique. 
Les utilisateurs peuvent télécharger les fichiers en cliquant sur les liens correspondants ou tout télécharger en cliquant 
sur Télécharger tous les fichiers dans un zip au bas de la page.

Pour exécuter le script, ouvrez un terminal, naviguez jusqu'au répertoire contenant le fichier "serveur.py", et exécutez la commande suivante:

Le serveur sera alors lancé et sera accessible à l'adresse http://10.0.0.236:5000/ depuis n'importe quel navigateur web sur le réseau local.'''

import os
from flask import Flask, send_file, make_response
from zipfile import ZipFile

app = Flask(__name__)

@app.route('/')
def file_list():
    file_list = []
    for root, dirs, files in os.walk('.'):
        for f in files:
            file_list.append(os.path.join(root, f))
    file_list.sort()
    file_links = ''
    for f in file_list:
        file_links += f'<p><a href="/download/{f}">{f}</a></p>'
    file_links += f'<p><a href="/download_all">Télécharger tous les fichiers dans un zip</a></p>'
    return file_links

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

@app.route('/download_all')
def download_all():
    file_list = []
    for root, dirs, files in os.walk('.'):
        for f in files:
            file_list.append(os.path.join(root, f))
    file_list.sort()
    zip_file_name = 'Tous_les_fichiers.zip'
    with ZipFile(zip_file_name, 'w') as zip:
        for file in file_list:
            zip.write(file)
    response = make_response(send_file(zip_file_name, as_attachment=True))
    response.headers['Content-Disposition'] = f'attachment; filename={zip_file_name}'
    return response

if __name__ == '__main__':
    app.run(host='10.0.0.236')
    


