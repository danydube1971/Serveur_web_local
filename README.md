# Serveur_web_local

Voici un script Python 3 pour Linux Mint qui utilise le module Flask pour lancer un serveur web local et afficher les 
fichiers du dossier courant dans le même emplacement que le script. Les autres utilisateurs du réseau local peuvent accéder 
au serveur en utilisant l'adresse IP 10.0.0.236 (qui est défini dans le script) et télécharger les fichiers de la page.

Assurez-vous d'installer le module Flask en exécutant la commande suivante dans votre terminal:

**pip3 install Flask**

Ce script crée un serveur Flask qui affiche une liste de fichiers dans le dossier courant et sous-dossiers en ordre alphabétique. 
Les utilisateurs dans le même réseau local peuvent télécharger les fichiers en cliquant sur les liens correspondants ou tout télécharger en cliquant 
sur Télécharger **tous les fichiers** dans un zip au bas de la page.

Pour exécuter le script, ouvrez un terminal, et exécutez la commande suivante:
**python3 "Serveur_fichiers_local.py"**

Le serveur sera alors lancé et sera accessible à l'adresse http://10.0.0.236:5000/ depuis n'importe quel navigateur web sur le réseau local.
Pour changer l'adresse l'adresse ip du serveur, vous devez le changer dans le script.
