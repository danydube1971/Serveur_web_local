Guide d'Utilisation du Script Serveur de Fichiers
=================================================
Ce guide te permet de comprendre et d'utiliser le script **Serveur_fichiers_local_GUI_v2.py** pour partager un dossier (ou un site web) sur ton réseau local (via un navigateur web) à partir d'une interface graphique simple. Suis les étapes ci-dessous pour démarrer.

![Serveur_fichiers_local_GUI_v12](https://github.com/user-attachments/assets/91a3f642-0ddb-4d67-a872-710d73eb22d4)


* * * * *
1\. Prérequis
-------------
Avant de commencer, assure-toi d'avoir installé les éléments suivants :
-   **Python 3.7+**\
    Vérifie ta version avec `python --version` dans ton terminal.
-   **Dépendances Python**\
    Installe les bibliothèques nécessaires avec pip :
    ```
    pip install PyQt6 flask werkzeug
    ```

-   **Accès à un terminal/Invite de commandes**\
    Pour lancer le script et voir d'éventuels messages de log.
* * * * *
2\. Présentation du Script
--------------------------
Ce script combine :
-   **Flask** pour créer un serveur web permettant de partager des fichiers.
-   **PyQt6** pour fournir une interface graphique conviviale.
-   Des fonctionnalités pour sélectionner un dossier, définir un port, démarrer et arrêter le serveur, et afficher les logs en temps réel.
* * * * *

3\. Installation et Lancement
-----------------------------
### a. Télécharger le Script
-   Clone ou télécharge le fichier `Serveur_fichiers_local_GUI_v2.py` depuis ton dépôt GitHub.
### b. Lancer le Script
-   Ouvre un terminal dans le dossier contenant le script.
-   Exécute-le avec la commande :
    ```
    python Serveur_fichiers_local_GUI_v2.py
    ```
-   Une fenêtre GUI devrait s'ouvrir.
* * * * *
4\. Utilisation de l'Interface Graphique
----------------------------------------
Une fois l'application lancée, voici comment l'utiliser :
### a. Sélection du Dossier à Partager
-   **Champ "Choisissez un dossier à partager"** : Clique sur le bouton **Parcourir** pour ouvrir une fenêtre de sélection de dossier.
-   Choisis le dossier que tu souhaites partager. Le chemin du dossier apparaîtra dans le champ de texte.
### b. Choix du Port
-   **Champ "Port réseau"** : Le port par défaut est `5000`. Tu peux modifier ce numéro si nécessaire.
-   Attention : certains ports (ex. 6000 à 6007, 6063) sont souvent bloqués par les navigateurs. Le script te préviendra si tu choisis l'un de ces ports.
### c. Démarrer le Serveur
-   Clique sur le bouton **Démarrer le Serveur**.
-   Le script vérifie que le dossier est sélectionné et que le port est valide.
-   Une fois démarré, l'adresse du serveur (par exemple, `http://192.168.x.x:5000`) s'affiche dans le champ dédié.
### d. Accéder au Serveur

-   Clique sur **Ouvrir la page du serveur** pour lancer ton navigateur par défaut et visualiser le contenu du dossier partagé.
-   Tu peux naviguer dans les fichiers, télécharger des fichiers ou accéder à une page `index.html` si elle existe dans le dossier.
* * * * *
5\. Fonctionnalités du Serveur
------------------------------
Le serveur Flask intégré gère :
-   **Navigation sécurisée** :\
    Seuls les fichiers et dossiers dans le dossier partagé sont accessibles.\
    Les accès non autorisés sont bloqués (code 403).
-   **Affichage dynamique des fichiers** :\
    Le serveur liste les dossiers et fichiers (avec leur taille en Mo) dans le dossier sélectionné.
-   **Téléchargement de fichiers** :\
    Via l'URL `/download/<nom_du_fichier>`, le téléchargement est possible avec un log affichant l'adresse IP du client et la date/heure.
-   **Logs** :\
    Les messages (démarrage, erreurs, téléchargements) s'affichent dans la zone de logs de l'interface.
* * * * *
6\. Arrêt du Serveur
--------------------
-   Pour arrêter le serveur, clique sur **Arrêter le Serveur** (le bouton change de texte lorsque le serveur est actif).
-   Le script arrête proprement le serveur Flask et libère le port utilisé.
* * * * *
7\. Conseils et Dépannage
-------------------------
-   **Vérifier le Port** :\
    Si le port est déjà utilisé par une autre application, le script affichera un message d'erreur. Choisis alors un autre port.

-   **Droits d'accès** :\
    Si tu rencontres des problèmes d'accès ou de permission, vérifie que le dossier sélectionné est accessible en lecture.
-   **Logs et messages** :\
    Consulte la zone de logs pour plus d'informations en cas de dysfonctionnement.
-   **Utilisation en réseau** :\
    Pour accéder au serveur depuis un autre appareil du réseau local, utilise l'adresse IP affichée dans l'interface.
