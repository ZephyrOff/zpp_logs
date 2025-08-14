# zpp_logs: Un Module de Logging Python Flexible et Puissant

`zpp_logs` est un module de logging Python conçu pour offrir une flexibilité maximale dans la configuration et l'utilisation des journaux d'événements. Inspiré par le module `logging` standard de Python, il introduit des fonctionnalités avancées telles que la configuration via YAML, le formatage basé sur Jinja2 avec des règles dynamiques, des filtres personnalisables et une gestion avancée des handlers.

## Fonctionnalités Clés

*   **Configuration Flexible** : Configurez l'intégralité de votre système de logging via un fichier YAML ou directement en Python.
*   **Niveaux de Log Personnalisés** : Inclut un niveau `SUCCESS` (25) en plus des niveaux standards.
*   **Formatage Avancé avec Jinja2** :
    *   Utilisez des templates Jinja2 pour définir le format de vos messages de log.
    *   Fonctions Jinja2 personnalisées (`fg`, `attr`, `date`, `epoch`) pour un formatage riche (ex: couleurs dans la console).
    *   **Règles de Formatage Dynamiques** : Appliquez des transformations conditionnelles aux champs de vos logs basées sur des expressions Jinja2, avec un comportement par défaut (`__default__`).
*   **Filtrage Puissant** : Filtrez les messages de log au niveau du handler en utilisant des expressions Jinja2.
*   **Handlers Multiples** :
    *   `ConsoleHandler` : Écrit les logs dans la console (stdout/stderr).
    *   `FileHandler` : Écrit les logs dans un fichier, avec rotation basée sur la taille (`maxBytes`, `backupCount`) et support du logging circulaire.
    *   `DatabaseHandler` : Enregistre les logs dans une base de données (SQLite, MySQL, etc.) avec mappage de colonnes personnalisable via Jinja2 et colonnes par défaut.
    *   `SMTPHandler` : Envoie les logs par e-mail via SMTP.
    *   `ResendHandler` : Envoie les logs par e-mail via l'API Resend.
*   **Modification Dynamique** : Modifiez les propriétés des formatters, handlers et loggers à la volée après leur création.

## Installation

1.  **Cloner le dépôt** (ou créer la structure de fichiers) :
    ```bash
    mkdir zpp_logs
    # Créez les fichiers .py à l'intérieur de zpp_logs/
    # Créez config.yaml et main.py à la racine
    ```
2.  **Installer les dépendances** :
    ```bash
    pip install -r requirements.txt
    ```
    Contenu de `requirements.txt` :
    ```
    pyyaml
    jinja2
    colorama
    requests
    SQLAlchemy
    ```

## Concepts Clés

### Niveaux de Log

Les niveaux de log sont des entiers, avec des constantes prédéfinies :
`CRITICAL` (50), `ERROR` (40), `WARNING` (30), `SUCCESS` (25), `INFO` (20), `DEBUG` (10), `NOTSET` (0).

### Loggers

Les loggers sont les points d'entrée pour enregistrer les messages. Ils possèdent un nom et une liste de handlers.

### Formatters

Définissent l'apparence des messages de log.
*   **`format_str`** : Une chaîne de template Jinja2 (ex: `"{{ date('%H:%M:%S') }} | {{ levelname }} | {{ msg }}"`).
*   **Règles (`rules`)** : Un dictionnaire où les clés sont des expressions Jinja2 (évaluées à `True` ou `False`) et les valeurs sont des dictionnaires de champs à modifier. La clé `__default__` agit comme une clause `else`.

    ```yaml
    # Exemple de règles dans un formatter
    rules:
        "levelname == 'SUCCESS'":
          levelname: "{{ fg('green') }}SUCCESS{{ attr(0) }}"
          msg: "{{ fg('green') }}Opération réussie : {{ msg }}{{ attr(0) }}"
        "levelname == 'ERROR' and 'database' in msg":
          levelname: "{{ fg('yellow') }}DB_ERROR{{ attr(0) }}"
          msg: "{{ fg('yellow') }}Problème de base de données: {{ msg }}{{ attr(0) }}"
        __default__:
          levelname: "{{ fg('gray') }}DEFAULT{{ attr(0) }}"
          msg: "{{ fg('gray') }}Message par défaut: {{ msg }}{{ attr(0) }}"
    ```

### Handlers

Les handlers sont responsables de l'envoi des messages de log vers des destinations spécifiques (console, fichier, base de données, e-mail, etc.). Chaque handler peut être configuré indépendamment.

*   **`level`** : Le niveau minimum du message pour que le handler le traite. Un message avec un niveau inférieur à celui du handler sera ignoré. Peut être une constante de `zpp_logs` (ex: `zpp_logs.INFO`) ou une chaîne de caractère (ex: `INFO`).
*   **`ops`** : L'opérateur de comparaison du niveau. Définit comment le niveau du message est comparé au `level` du handler.
    *   `">="` (par défaut) : Le handler traite les messages dont le niveau est supérieur ou égal à son `level`.
    *   `">"` : Strictement supérieur.
    *   `"<="` : Inférieur ou égal.
    *   `"<"` : Strictement inférieur.
    *   `"=="` : Égal.
    *   `"!="` : Différent.
*   **`formatter`** : Le nom de l'instance du formatter à utiliser pour ce handler, tel que défini dans la section `formatters` du `config.yaml`.
*   **`filters`** : Une liste d'expressions Jinja2. Si une expression évalue à `False` pour un message donné, ce message est filtré et n'est pas traité par le handler. Utile pour des filtrages complexes basés sur le contenu du message ou d'autres attributs du record de log.

#### ConsoleHandler

Écrit les logs dans la console (sortie standard ou erreur standard).

*   **`output`** : Spécifie la destination de la sortie. Peut être `sys.stdout` (par défaut) ou `sys.stderr`.

    ```yaml
    # Exemple de ConsoleHandler dans config.yaml
    handlers:
        console_stdout:
            class: zpp_logs.ConsoleHandler
            level: zpp_logs.INFO
            ops: ">="
            formatter: standard
            filters:
                - "'secret' not in msg" # Filtre les messages contenant le mot 'secret'
            output: sys.stdout # Logs vers la sortie standard
        console_stderr:
            class: zpp_logs.ConsoleHandler
            level: zpp_logs.ERROR
            ops: ">="
            formatter: standard
            output: sys.stderr # Logs d'erreur vers la sortie d'erreur standard
    ```

#### FileHandler

Écrit les logs dans un fichier, avec des options avancées de rotation.

*   **`filename`** : Le chemin du fichier de log. Peut inclure des expressions Jinja2 pour des noms de fichiers dynamiques (ex: par date).
*   **`maxBytes`** : La taille maximale du fichier de log en octets avant rotation. Si `0`, la taille n'est pas limitée.
*   **`backupCount`** : Le nombre de fichiers de backup à conserver après rotation.
    *   Si `backupCount > 0` : Rotation standard. Quand le fichier atteint `maxBytes`, il est renommé (ex: `app.log.1`, `app.log.2`, etc.) et un nouveau fichier est créé. Les anciens backups sont supprimés si leur nombre dépasse `backupCount`.
    *   Si `backupCount == 0` et `maxBytes > 0` : Logging circulaire. Quand le fichier atteint `maxBytes`, la plus ancienne ligne est supprimée pour faire de la place à la nouvelle. Le fichier ne grossit jamais au-delà de `maxBytes`.

    ```yaml
    # Exemple de FileHandler dans config.yaml
    handlers:
        file_daily:
            class: zpp_logs.FileHandler
            level: zpp_logs.INFO
            formatter: standard
            filename: "logs/app_{{ date('%Y-%m-%d') }}.log" # Nom de fichier quotidien
            maxBytes: 0 # Pas de limite de taille
            backupCount: 0 # Pas de rotation
        file_rotated:
            class: zpp_logs.FileHandler
            level: zpp_logs.INFO
            formatter: standard
            filename: "logs/rotated_app.log"
            maxBytes: 1048576 # 1 MB
            backupCount: 5 # Garde 5 fichiers de backup (rotated_app.log.1, .2, etc.)
        file_circular:
            class: zpp_logs.FileHandler
            level: zpp_logs.DEBUG
            formatter: standard
            filename: "logs/circular_debug.log"
            maxBytes: 524288 # 512 KB
            backupCount: 0 # Active le logging circulaire
    ```

#### DatabaseHandler

Enregistre les logs dans une base de données (supporte SQLite, MySQL, etc.).

*   **`model`** : (Optionnel) Permet de spécifier un modèle de table SQLAlchemy. C'est la méthode recommandée pour un contrôle précis du schéma de la table.
    *   En configuration YAML, fournissez le chemin d'importation du modèle : `model: 'mon_app.models.LogEntry'`.
    *   En configuration programmatique, passez directement la classe du modèle : `model=LogEntry`.
    *   Si un modèle est fourni, le handler utilisera son schéma pour créer la table (si elle n'existe pas). Les paramètres `table` et `columns` deviennent alors facultatifs.

*   **`connector`** : Un dictionnaire spécifiant les détails de connexion à la base de données.
    *   `engine` : Le type de base de données (ex: `sqlite`, `mysql`).
    *   Pour `sqlite` : `filename` (chemin du fichier de base de données).
    *   Pour `mysql` : `host`, `user`, `password`, `database`.
    *   `table` : Le nom de la table où les logs seront stockés (par défaut: `logs`).
*   **`columns`** : (Optionnel) Un dictionnaire pour mapper les attributs du record de log aux noms de colonnes de la table. Les valeurs peuvent être des expressions Jinja2. Si non spécifié, des colonnes par défaut (`timestamp`, `level`, `logger_name`, `message`) sont utilisées.

    ```yaml
    # Exemple de DatabaseHandler dans config.yaml
    handlers:
        db_sqlite:
            class: zpp_logs.DatabaseHandler
            level: zpp_logs.INFO
            formatter: standard
            connector:
                engine: sqlite
                filename: "logs/app_logs.db"
                table: "application_events"
            columns: # Mappage personnalisé des colonnes
                event_time: "date('%Y-%m-%d %H:%M:%S')" # Renomme 'timestamp' en 'event_time'
                log_level: "levelname" # Renomme 'level' en 'log_level'
                source: "name" # Renomme 'logger_name' en 'source'
                full_message: "msg" # Renomme 'message' en 'full_message'
                user_id: "user_id if 'user_id' in record else 'N/A'" # Ajoute une colonne conditionnelle
        db_mysql:
            class: zpp_logs.DatabaseHandler
            level: zpp_logs.WARNING
            formatter: standard
            connector:
                engine: mysql
                host: localhost
                user: loguser
                password: logpassword
                database: myapp_logs_db
            # Utilise les colonnes par défaut si 'columns' n'est pas spécifié

**Exemple avec un modèle SQLAlchemy**

1.  **Définissez votre modèle SQLAlchemy :**

    ```python
    # dans un fichier models.py
    from sqlalchemy.orm import declarative_base
    from sqlalchemy import Column, Integer, String, DateTime
    from datetime import datetime

    Base = declarative_base()

    class LogEntry(Base):
        __tablename__ = 'log_entries'
        id = Column(Integer, primary_key=True)
        timestamp = Column(DateTime, default=datetime.utcnow)
        level = Column(String(50))
        message = Column(String)
        logger_name = Column(String(100))
        user_id = Column(Integer) # Exemple de colonne personnalisée
    ```

2.  **Configurez le handler pour utiliser ce modèle :**

    *En `config.yaml` :*
    ```yaml
    handlers:
        db_with_model:
            class: zpp_logs.DatabaseHandler
            level: zpp_logs.INFO
            formatter: standard
            connector:
                engine: sqlite
                filename: "logs/app_with_model.db"
            model: 'models.LogEntry' # Chemin d'importation du modèle
    ```

    *En Python :*
    ```python
    # from models import LogEntry
    db_handler_model = DatabaseHandler(
        level=INFO,
        formatter=standard_formatter,
        connector={"engine": "sqlite", "filename": "logs/app_with_model.db"},
        model=LogEntry # Passez la classe du modèle directement
    )
    ```
    ```

#### SMTPHandler

Envoie les logs par e-mail via un serveur SMTP. Idéal pour les alertes critiques.

*   **`host`** : L'adresse du serveur SMTP.
*   **`port`** : Le port du serveur SMTP (souvent 25, 587 pour TLS, 465 pour SSL).
*   **`username`** : Nom d'utilisateur pour l'authentification SMTP.
*   **`password`** : Mot de passe pour l'authentification SMTP.
*   **`fromaddr`** : L'adresse e-mail de l'expéditeur.
*   **`toaddrs`** : Une liste d'adresses e-mail des destinataires.
*   **`subject`** : Le sujet de l'e-mail. Peut inclure des expressions Jinja2 pour des sujets dynamiques.

    ```yaml
    # Exemple de SMTPHandler dans config.yaml
    handlers:
        email_critical:
            class: zpp_logs.SMTPHandler
            level: zpp_logs.CRITICAL
            formatter: standard
            host: smtp.your-email-provider.com
            port: 587
            username: your_email@example.com
            password: your_email_password
            fromaddr: "no-reply@your-app.com"
            toaddrs: ["admin@your-app.com", "devops@your-app.com"]
            subject: "ALERTE CRITIQUE: {{ levelname }} dans {{ name }} à {{ date('%Y-%m-%d %H:%M:%S') }}"
    ```

#### ResendHandler

Envoie les logs par e-mail en utilisant l'API Resend. Nécessite une clé API Resend.

*   **`api_key`** : Votre clé API Resend (commence par `re_`).
*   **`fromaddr`** : L'adresse e-mail de l'expéditeur (doit être un domaine vérifié dans Resend).
*   **`to`** : Une liste d'adresses e-mail des destinataires.
*   **`subject`** : Le sujet de l'e-mail. Peut inclure des expressions Jinja2.

    ```yaml
    # Exemple de ResendHandler dans config.yaml
    handlers:
        email_resend:
            class: zpp_logs.ResendHandler
            level: zpp_logs.ERROR
            formatter: standard
            api_key: re_YOUR_RESEND_API_KEY_HERE # Remplacez par votre vraie clé API
            fromaddr: "onboarding@your-verified-domain.com"
            to: ["support@your-app.com"]
            subject: "ERREUR APPLICATION: {{ levelname }} détectée dans {{ name }}"
    ```

### Journalisation Asynchrone

Pour les handlers qui peuvent être lents (comme l'envoi d'e-mails avec `SMTPHandler` ou l'écriture dans une base de données distante), `zpp_logs` offre un mode de journalisation asynchrone. Lorsqu'il est activé, le handler s'exécute dans un thread d'arrière-plan, ce qui empêche votre application principale de se bloquer.

Pour activer le mode asynchrone pour un handler, ajoutez simplement `async_mode: true` à sa configuration dans votre fichier `config.yaml`.

**Exemple : Rendre le `SMTPHandler` asynchrone**

```yaml
# Exemple de SMTPHandler asynchrone dans config.yaml
handlers:
    email_critical_async:
        class: zpp_logs.SMTPHandler
        level: zpp_logs.CRITICAL
        async_mode: true  # Active le mode asynchrone
        formatter: standard
        host: smtp.your-email-provider.com
        port: 587
        username: your_email@example.com
        password: your_email_password
        fromaddr: "no-reply@your-app.com"
        toaddrs: ["admin@your-app.com"]
        subject: "ALERTE CRITIQUE (Async): {{ levelname }} dans {{ name }}"
```

C'est tout ! Ce handler enverra maintenant les e-mails en arrière-plan sans ralentir votre application. Cette fonctionnalité peut être appliquée à n'importe quel handler.

De même, lors de la création d'un handler en Python, vous pouvez l'activer en passant `async_mode=True` à son constructeur.

**Exemple : Rendre le `ConsoleHandler` asynchrone en Python**

```python
# Exemple de ConsoleHandler asynchrone en Python
mon_handler_console = ConsoleHandler(
    level=INFO,
    formatter=mon_formatter,
    async_mode=True  # Active le mode asynchrone
)

logger = Logger(name="mon_logger", handlers=[mon_handler_console])
logger.info("Ce message sera traité en arrière-plan.")
print("Ce print s'exécute immédiatement.")
```

### 2. Configuration Programmatique

La configuration programmatique vous permet de construire et de gérer votre système de logging directement dans votre code Python, offrant une flexibilité maximale et un contrôle précis sur chaque composant.

#### Imports Nécessaires

Pour commencer, importez les classes et constantes essentielles :

```python
from zpp_logs import (
    Logger, CustomFormatter, ConsoleHandler, FileHandler, DatabaseHandler,
    SMTPHandler, ResendHandler,
    DEBUG, INFO, WARNING, ERROR, CRITICAL, SUCCESS
)
import sys
import os
from sqlalchemy import create_engine, text # Pour la vérification de la base de données
```

#### 2.1. Création d'un Formatter

Un formatter définit l'apparence de vos messages de log. Vous pouvez spécifier un format de base avec `format_str` (supportant Jinja2) et ajouter des règles de formatage dynamiques.

```python
# Création d'un formatter de base
programmatic_formatter = CustomFormatter(
    format_str="[PROG] {{ date('%H:%M:%S') }} | {{ levelname }} | {{ msg }}"
)

# Ajout de règles dynamiques au formatter
# Ces règles modifient l'apparence des champs 'levelname' ou 'msg' en fonction de conditions
programmatic_formatter.set_rule(
    "levelname == 'INFO'",
    {"levelname": "{{ fg('cyan') }}INFO{{ attr(0) }}"}
)
programmatic_formatter.set_rule(
    "levelname == 'WARNING'",
    {"msg": "{{ fg('yellow') }}WARNING: {{ msg }}{{ attr(0) }}"}
)
programmatic_formatter.set_rule(
    "__default__",
    {"levelname": "{{ fg('magenta') }}PROG_DEFAULT{{ attr(0) }}"}
)
```

#### 2.2. Création des Handlers

Les handlers dirigent les messages de log formatés vers différentes destinations. Chaque handler est configuré avec un niveau minimum, un opérateur de comparaison, un formatter et des filtres optionnels.

##### ConsoleHandler

Envoie les logs à la console (stdout ou stderr).

```python
# ConsoleHandler: envoie les logs INFO et supérieurs à la sortie standard
programmatic_console_handler = ConsoleHandler(
    level=INFO,
    formatter=programmatic_formatter,
    output=sys.stdout
)
```

##### FileHandler

Écrit les logs dans un fichier, avec des options de rotation avancées.

```python
# FileHandler: écrit les logs DEBUG et supérieurs dans un fichier avec rotation
programmatic_file_handler = FileHandler(
    level=DEBUG,
    formatter=programmatic_formatter,
    filename="logs/programmatic_app.log",
    maxBytes=512,
    backupCount=1
)
```

##### DatabaseHandler

Enregistre les logs dans une base de données. Supporte SQLite, MySQL, etc., avec mappage de colonnes personnalisable.

```python
# DatabaseHandler: enregistre les logs INFO et supérieurs dans une base SQLite
# Assurez-vous que le fichier DB n'existe pas pour un test propre
if os.path.exists("logs/programmatic_db.db"): os.remove("logs/programmatic_db.db")
programmatic_db_handler = DatabaseHandler(
    level=INFO,
    formatter=programmatic_formatter,
    connector={
        "engine": "sqlite",
        "filename": "logs/programmatic_db.db",
        "table": "prog_logs"
    },
    columns={
        "timestamp": "date('%Y-%m-%d %H:%M:%S')",
        "level": "levelname",
        "message": "msg"
    }
)
```

##### SMTPHandler

Envoie les logs par e-mail via un serveur SMTP.

```python
# SMTPHandler: envoie les logs CRITICAL et supérieurs par e-mail
programmatic_smtp_handler = SMTPHandler(
    level=CRITICAL,
    formatter=programmatic_formatter,
    host="smtp.mailtrap.io",
    port=2525,
    username="your_mailtrap_username",
    password="your_mailtrap_password",
    fromaddr="programmatic@example.com",
    toaddrs=["admin@programmatic.com"],
    subject="[PROG] ALERTE CRITIQUE: {{ levelname }} de {{ name }}"
)
```

##### ResendHandler

Envoie les logs par e-mail via l'API Resend.

```python
# ResendHandler: envoie les logs ERROR et supérieurs via l'API Resend
programmatic_resend_handler = ResendHandler(
    level=ERROR,
    formatter=programmatic_formatter,
    api_key="re_YOUR_RESEND_API_KEY",
    fromaddr="onboarding@programmatic.dev",
    to=["dev@programmatic.dev"],
    subject="[PROG] ERREUR: {{ levelname }} de {{ name }}"
)
```

#### 2.3. Création du Logger

Un logger est le point d'entrée pour enregistrer vos messages. Il regroupe un ensemble de handlers.

```python
# Création d'un logger et association des handlers
programmatic_logger = Logger(name="programmatic_logger", handlers=[
    programmatic_console_handler,
    programmatic_file_handler,
    programmatic_db_handler,
    programmatic_smtp_handler,
    programmatic_resend_handler
])
```

#### 2.4. Utilisation du Logger

Une fois configuré, utilisez le logger pour enregistrer vos messages.

```python
# Enregistrement de messages de différents niveaux
programmatic_logger.info("Ceci est un message info du logger programmatique.")
programmatic_logger.warning("Ceci est un message d'avertissement du logger programmatique.")
programmatic_logger.error("Ceci est un message d'erreur du logger programmatique.")
programmatic_logger.info("Ce message contient des informations secrètes du logger programmatique.") # Devrait être filtré par le ConsoleHandler
programmatic_logger.critical("Ceci est un message critique qui devrait envoyer un e-mail.")

# Exemple de vérification: lecture des logs depuis la base de données
prog_db_engine = create_engine("sqlite:///logs/programmatic_db.db")
with prog_db_engine.connect() as conn:
    result = conn.execute(text("SELECT timestamp, level, message FROM prog_logs ORDER BY timestamp DESC LIMIT 3"))
    print("\n--- Derniers 3 logs de la DB programmatique ---")
    for row in result:
        print(f"Timestamp: {row.timestamp}, Level: {row.level}, Message: {row.message}")
```


## Modification Dynamique

Les objets `Logger`, `CustomFormatter` et les instances de `BaseHandler` (et ses sous-classes) exposent des méthodes pour modifier leur comportement après leur création.

### Modification des Formatters

```python
# Supposons 'my_formatter' est une instance de CustomFormatter
# my_formatter = CustomFormatter(...)

# Ajouter/Modifier une règle
my_formatter.set_rule(
    "levelname == 'ERROR'",
    {"levelname": "{{ fg('red') }}DYNAMIC_ERROR{{ attr(0) }}"}
)

# Supprimer une règle
my_formatter.delete_rule("levelname == 'WARNING'")

# Les logs suivants utiliseront les règles modifiées
# programmatic_logger.error("Un message d'erreur dynamique.")
```

### Modification des Handlers

```python
# Supposons 'my_handler' est une instance de ConsoleHandler, FileHandler, etc.
# my_handler = ConsoleHandler(...)

# Changer le niveau
my_handler.set_level(DEBUG)

# Changer l'opérateur de comparaison
my_handler.set_ops('==') # N'acceptera que les messages de niveau DEBUG

# Ajouter un filtre
my_handler.add_filter("'nouvel_element' not in msg")

# Supprimer un filtre
my_handler.remove_filter("'secret' not in msg")

# Changer le formatter (si le handler a été créé avec un formatter)
# my_handler.set_formatter(un_autre_formatter)
```

### Modification des Loggers

```python
# Supposons 'my_logger' est une instance de Logger
# my_logger = Logger(...)

# Ajouter un handler
my_logger.add_handler(programmatic_file_handler)

# Supprimer un handler
my_logger.remove_handler(programmatic_console_handler)
```

## Fonctions jinja2 étendues

*   **Fonctions Jinja2 personnalisées** : Ces fonctions peuvent être utilisées directement dans votre chaîne de formatage ou dans les règles. Elles permettent d'accéder à des informations contextuelles très riches.

    *   **Formatage et Attributs :**
        *   `fg(color_name)` : Applique une couleur de premier plan au texte suivant. `color_name` peut être `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`, ou des noms spécifiques comme `deep_sky_blue_3a` (cyan), `medium_purple_4` (magenta), `grey_46` (blanc).
            *   Exemple : "{{ fg('green') }}Mon message en vert{{ attr(0) }}"
        *   `bg(color_name)` : Applique une couleur d'arrière-plan au texte suivant. Utilise les mêmes `color_name` que `fg()`.
            *   Exemple : "{{ bg('blue') }}Texte sur fond bleu{{ attr(0) }}"
        *   `attr(code)` : Applique des attributs de texte. Le code `0` réinitialise tous les styles (couleur, gras, etc.).
            *   Exemple : "{{ fg('red') }}Texte rouge{{ attr(0) }} Texte normal"

    *   **Date et Heure :**
        *   `date(format_str)` : Formate la date et l'heure actuelles. `format_str` suit les codes de formatage de `strftime` de Python (ex: `%Y-%m-%d %H:%M:%S`).
            *   Exemple : "Log du {{ date('%Y-%m-%d %H:%M') }}"
        *   `epoch()` : Renvoie le timestamp Unix actuel (nombre de secondes depuis l'époque).
            *   Exemple : "Timestamp: {{ epoch() }}"

    *   **Informations sur le Code Source :**
        *   `exc_info()` : Renvoie les informations sur l'exception courante (type, valeur, traceback). Utile dans les blocs `try...except`.
            *   Exemple : "Exception: {{ exc_info() }}"
        *   `filename()` : Renvoie le nom du fichier Python où l'appel de log a été effectué.
            *   Exemple : "Fichier: {{ filename() }}"
        *   `filepath()` : Renvoie le chemin absolu du répertoire contenant le fichier Python où l'appel de log a été effectué.
            *   Exemple : "Chemin du fichier: {{ filepath() }}"
        *   `lineno()` : Renvoie le numéro de ligne dans le fichier Python où l'appel de log a été effectué.
            *   Exemple : "Ligne: {{ lineno() }}"
        *   `functname()` : Renvoie le nom de la fonction ou méthode Python où l'appel de log a été effectué.
            *   Exemple : "Fonction: {{ functname() }}"

    *   **Informations sur le Système de Fichiers / Chemin :**
        *   `path()` : Renvoie le chemin absolu du répertoire de travail actuel.
            *   Exemple : "CWD: {{ path() }}"

    *   **Informations sur le Processus :**
        *   `process()` : Renvoie le nom du processus Python actuel.
            *   Exemple : "Processus: {{ process() }}"
        *   `processid()` : Renvoie l'ID du processus Python actuel.
            *   Exemple : "PID: {{ processid() }}"

    *   **Informations sur l'Utilisateur :**
        *   `username()` : Renvoie le nom d'utilisateur du système.
            *   Exemple : "Utilisateur: {{ username() }}"
        *   `uid()` : Renvoie l'ID utilisateur (UID) du système.
            *   Exemple : "UID: {{ uid() }}"

    *   **Informations sur le Système d'Exploitation :**
        *   `os_name()` : Renvoie le nom du système d'exploitation (ex: `Windows`, `Linux`, `Darwin`).
            *   Exemple : "OS: {{ os_name() }}"
        *   `os_version()` : Renvoie la version détaillée du système d'exploitation.
            *   Exemple : "Version OS: {{ os_version() }}"
        *   `os_release()` : Renvoie la version du système d'exploitation (ex: `10`, `20.04`).
            *   Exemple : "Release OS: {{ os_release() }}"
        *   `platform()` : Renvoie une chaîne d'identification de la plateforme (ex: `Windows-10-10.0.19045-SP0`).
            *   Exemple : "Plateforme: {{ platform() }}"
        *   `os_archi()` : Renvoie l'architecture du système d'exploitation (ex: `64bit`).
            *   Exemple : "Architecture OS: {{ os_archi() }}"

    *   **Informations sur la Mémoire (RAM) :**
        *   `mem_total()` : Mémoire RAM totale du système.
        *   `mem_available()` : Mémoire RAM disponible.
        *   `mem_used()` : Mémoire RAM utilisée.
        *   `mem_free()` : Mémoire RAM libre.
        *   `mem_percent()` : Pourcentage de mémoire RAM utilisée.
            *   Exemple : "RAM: {{ mem_used() }} / {{ mem_total() }} ({{ mem_percent() }}%)"

    *   **Informations sur la Mémoire Swap :**
        *   `swap_total()` : Mémoire Swap totale.
        *   `swap_used()` : Mémoire Swap utilisée.
        *   `swap_free()` : Mémoire Swap libre.
        *   `swap_percent()` : Pourcentage de mémoire Swap utilisée.
            *   Exemple : "Swap: {{ swap_used() }} / {{ swap_total() }} ({{ swap_percent() }}%)"

    *   **Informations sur le CPU :**
        *   `cpu_count()` : Nombre de cœurs physiques du CPU.
        *   `cpu_logical_count()` : Nombre de cœurs logiques (incluant les threads) du CPU.
        *   `cpu_percent()` : Pourcentage d'utilisation du CPU (sur un court intervalle).
            *   Exemple : "CPU: {{ cpu_percent() }}% ({{ cpu_logical_count() }} cœurs)"

    *   **Informations sur le Disque Actuel (du fichier de log) :**
        *   `current_disk_device()` : Nom du périphérique de disque (ex: `C:\`).
        *   `current_disk_mountpoint()` : Point de montage du disque.
        *   `current_disk_fstype()` : Type de système de fichiers (ex: `NTFS`).
        *   `current_disk_total()` : Taille totale du disque.
        *   `current_disk_used()` : Espace utilisé sur le disque.
        *   `current_disk_free()` : Espace libre sur le disque.
        *   `current_disk_percent()` : Pourcentage d'utilisation du disque.
            *   Exemple : "Disque ({{ current_disk_device() }}): {{ current_disk_used() }} / {{ current_disk_total() }} ({{ current_disk_percent() }}%)"

    *   **Fonctions Utilitaires :**
        *   `re_match(regex_pattern, value)` : Tente de faire correspondre `regex_pattern` au début de `value`. Renvoie un objet match si trouvé, `None` sinon.
            *   Exemple : "Match: {{ re_match('^(Error|Warning)', levelname) is not none }}"


## Extensibilité

Le module est conçu pour être facilement extensible :
*   **Nouveaux Handlers** : Créez de nouvelles classes héritant de `BaseHandler` et implémentez la méthode `emit`. Ajoutez-les à `_handler_class_map`.
*   **Nouvelles Fonctions Jinja2** : Définissez de nouvelles fonctions Python et ajoutez-les aux `globals` des environnements Jinja2 (`env`, `filter_env`, `filename_env`, etc.) où vous souhaitez les utiliser.
*   **Nouveaux Types de Colonnes DB** : Étendez `DatabaseHandler` pour supporter plus de types de colonnes SQLAlchemy.

---
