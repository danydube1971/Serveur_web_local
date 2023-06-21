# Serveur_web_local

Voici un script Python 3 pour Linux Mint qui utilise le module Flask pour lancer un serveur web local et afficher les 
fichiers du dossier courant dans le même emplacement que le script. Les autres utilisateurs du réseau local peuvent accéder 
au serveur en utilisant l'adresse IP 10.0.0.236 (qui est défini dans le script) par le port 5000 et télécharger les fichiers de la page.

![Serveur_local_01](https://github.com/danydube1971/Serveur_web_local/assets/74633244/fe3c7e08-c27f-4647-a67d-0df1625bdf0e)
![2023-06-21 18 17 15 10 0 0 236 a557f054504a](https://github.com/danydube1971/Serveur_web_local/assets/74633244/07a1ad05-c175-4e16-8f43-cb27982718da)


Assurez-vous d'installer le module Flask en exécutant la commande suivante dans votre terminal:

**pip3 install Flask**

Ce script crée un serveur Flask qui affiche une liste de fichiers dans le dossier courant et sous-dossiers en ordre alphabétique. 
Les utilisateurs dans le même réseau local peuvent télécharger les fichiers en cliquant sur les liens correspondants ou tout télécharger en cliquant 
sur Télécharger **tous les fichiers** dans un zip au bas de la page.

------------
**Comment exécuter le serveur**

Pour exécuter le script, placer le script dans le même dossier que les fichiers à partager. 

Ouvrez un terminal, et exécutez la commande suivante:
**python3 "Serveur_fichiers_local.py"**

Le serveur sera alors lancé et sera accessible à l'adresse http://10.0.0.236:5000/ depuis n'importe quel navigateur web sur le réseau local.
Pour changer l'adresse l'adresse ip du serveur, vous devez le changer dans le script à la ligne 55.
