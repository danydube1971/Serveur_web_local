'''Voici un script Python 3 pour Linux Mint qui utilise le module Flask pour lancer un serveur web local et afficher les fichiers du dossier courant dans le même emplacement que le script. Les autres utilisateurs du réseau local peuvent accéder au serveur en utilisant l'adresse IP 10.0.0.236 et télécharger les fichiers de la page.

Assurez-vous d'installer le module Flask en exécutant la commande suivante dans votre terminal:
pip3 install Flask

Ce script crée un serveur Flask qui affiche une liste de fichiers dans le dossier courant. Les utilisateurs peuvent télécharger les fichiers en cliquant sur les liens correspondants.

Pour exécuter le script, ouvrez un terminal, naviguez jusqu'au répertoire contenant le fichier "serveur.py", et exécutez la commande suivante:

Le serveur sera alors lancé et sera accessible à l'adresse http://10.0.0.236:5000/ depuis n'importe quel navigateur web sur le réseau local.'''


import os
from flask import Flask, send_file

app = Flask(__name__)

@app.route('/')
def file_list():
    file_list = os.listdir('.')
    file_links = ''
    for f in file_list:
        file_links += f'<p><a href="/download/{f}">{f}</a></p>'
    return file_links

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='10.0.0.236')

