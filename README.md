**Serveur de fichiers local avec interface graphique (Qt + Flask)**
===================================================================

Ce script permet de lancer un **serveur de fichiers local** (ou d'afficher une page web index.html) via **Flask**, avec une interface graphique développée en **PyQt6**. Il permet de **partager un dossier** via un serveur HTTP accessible sur le réseau local.

![Serveur_fichiers_local_GUI_v28](https://github.com/user-attachments/assets/2836f360-cbe5-4528-b280-a20a2bbf9765)


* * * * *

**1\. Pré-requis**
------------------

Avant d'exécuter le script, assurez-vous d'avoir les dépendances suivantes installées :

### **Dépendances Python :**

Vous devez installer **PyQt6** et **Flask** si ce n'est pas déjà fait. Ouvrez un terminal et exécutez :

```
pip install PyQt6 Flask Werkzeug
```

### **Autres pré-requis :**

-   **Linux Mint** (compatible avec d'autres distributions Linux et Windows)

-   **Python 3.12** ou une version compatible

-   **Télécharger le dossier « templates »** qui contient le fichier list_files.index.

-   **Télécharger le script Serveur_fichiers_local_GUI_v3.py**

* * * * *

**2\. Lancer le script**
------------------------

Ouvrez un terminal dans le dossier où se trouve le script et exécutez :

```
python Serveur_fichiers_local_GUI_v3.py
```

Si vous utilisez **Python 3.12** explicitement, utilisez :

```
python3 Serveur_fichiers_local_GUI_v3.py
```

L'interface graphique du serveur devrait s'afficher.

* * * * *

**3\. Utilisation de l'interface graphique**
--------------------------------------------

### **Sélectionner un dossier à partager**

1.  Cliquez sur **Parcourir** et sélectionnez un dossier.

2.  Vérifiez que le chemin apparaît dans la barre de texte.

### **Configurer le port**

-   Par défaut, le serveur utilise le port **8080**.

-   Vous pouvez modifier ce port si nécessaire, mais évitez les **ports bloqués** (6000-6007, 6063).

-   **Attention** : Si un autre programme utilise déjà ce port, vous devrez en choisir un autre.

### **Démarrer le serveur**

-   Cliquez sur **"Démarrer le Serveur"**.

-   L'adresse locale du serveur s'affiche (ex. `http://192.168.X.X:8080`).

-   Vous pouvez copier cette adresse et l'ouvrir dans un navigateur.

### **Accéder aux fichiers**

-   Les fichiers du dossier partagé sont listés dans le navigateur.

-   Vous pouvez **télécharger** un fichier en cliquant dessus.

### **Gérer les extensions autorisées**

-   Par défaut, seules certaines extensions sont accessibles (`.txt`, `.jpg`, `.mp3`, etc.).

-   Vous pouvez **modifier cette liste** en entrant d'autres extensions dans le champ **Extensions autorisées**.

### **Arrêter le serveur**

-   Cliquez sur **"Arrêter le Serveur"**.

-   Tous les partages sont fermés immédiatement.

### **Vérifier les logs**

-   La fenêtre affiche l'état du serveur et les événements (connexion d'un client, accès à un fichier...).

-   Vous pouvez **effacer les logs** avec le bouton dédié.

* * * * *

**4\. Accès depuis un autre appareil**
--------------------------------------

Si vous voulez accéder au serveur depuis un autre appareil du **même réseau** :

1.  Notez l'adresse locale affichée (`http://192.168.X.X:8080`).

2.  Saisissez-la dans un navigateur sur un autre PC ou téléphone connecté au **même Wi-Fi**.

3.  Vous devriez voir la liste des fichiers partagés.

**⚠ Remarque :** Pour un accès depuis l'extérieur (Internet), il faudra configurer une **redirection de port** sur votre routeur, ce qui n'est pas recommandé pour la sécurité.

* * * * *

