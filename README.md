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

#### Approche dynamique

##### 1. Instanciation d'un Logger
Un Logger a besoin d'un nom (name) et d'une liste de handlers pour être créé.

```python
from zpp_logs.core import Logger, CustomFormatter
from zpp_logs.handlers.console import ConsoleHandler
from zpp_logs.levels import DEBUG

# Étape 1: Créer un formateur
my_formatter = CustomFormatter("{{ levelname }}: {{ msg }}")

# Étape 2: Créer un ou plusieurs handlers
console_handler = ConsoleHandler(level=DEBUG, formatter=my_formatter)

# Étape 3: Créer le logger
logger = Logger(
    name="my_app",
    handlers=[console_handler]
)
```

##### 2. Émission de Logs
Une fois le logger créé, utilisez ses méthodes de niveau pour émettre des messages.

```python
logger.debug("Information de débogage détaillée.")
logger.info("Démarrage du processus.")
logger.warning("Le disque est presque plein.")
logger.error("Impossible de contacter le service externe.")
logger.critical("Échec critique, arrêt de l'application.")
```


##### 3. Passer des Données Supplémentaires
Une fonctionnalité clé est la capacité de passer des données structurées en utilisant des arguments clé-valeur (**kwargs). Ces données sont ajoutées au record du log et deviennent disponibles dans votre CustomFormatter (à la fois pour le formatage et pour les règles).

```python
# Le formateur peut utiliser 'user_id' et 'ip_address'
formatter = CustomFormatter("{{ msg }} (user: {{ user_id }}, ip: {{ ip_address }})")
logger.add_handler(ConsoleHandler(level=DEBUG, formatter=formatter))


# Passez les données en kwargs lors de l'appel de log
logger.info(
    "Tentative de connexion de l'utilisateur.",
    user_id="alice",
    ip_address="192.168.1.100"
)
# Sortie: Tentative de connexion de l'utilisateur. (user: alice, ip: 192.168.1.100)
```

#### Approche par instance de config

```python
from zpp_logs.core import LogManager

# Une seule instance de manager pour toute l'application
manager = LogManager('config.yaml')

# Obtenir le logger nommé 'database'
db_logger = manager.get_logger('database')
db_logger.debug("Connexion à la base de données...") # Ira dans app.log

# Obtenir le logger 'root'
root_logger = manager.get_logger('root')
root_logger.info("Message d'information général.") # Ira dans la console

# Demander un logger qui n'est pas dans la config
# Le LogManager renverra la configuration du logger 'root' !
api_logger = manager.get_logger('external_api')
api_logger.warning("Problème avec l'API externe.") # Ira dans la console
```

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

### ConsoleHandler

Le `ConsoleHandler` est conçu pour afficher les messages de log directement dans la console (sortie standard ou erreur standard).

#### Fonctionnalité

Ce handler est l'un des plus simples. Il prend un message de log, le formate en utilisant le `CustomFormatter` fourni, et l'écrit sur le flux de sortie spécifié, qui est par défaut `sys.stdout` (la sortie standard). Il est idéal pour le développement ou pour les applications en ligne de commande où une visibilité immédiate des logs est nécessaire.

#### Options

| Paramètre | Type | Défaut | Description |
|-----------|------|---------|-------------|
| `level` | `int` | `NOTSET` | Le niveau de log minimum requis pour que le message soit traité par ce handler. Doit être une constante de `zpp_logs.levels` (ex: `INFO`, `DEBUG`). |
| `formatter`| `CustomFormatter` | `None` | Une instance de `CustomFormatter` chargée de mettre en forme le message avant son affichage. |
| `filters` | `list` | `None` | Une liste de chaînes de caractères. Chaque chaîne est une expression Jinja2 qui doit retourner `True` pour que le log soit traité. |
| `output` | `str` | `'sys.stdout'` | Le flux de sortie. Peut être `'sys.stdout'` ou `'sys.stderr'`. |
| `ops` | `str` | `'>='` | L'opérateur de comparaison pour le niveau (`>=`, `==`, etc.). |
| `async_mode` | `bool` | `False` | Si `True`, les logs sont traités dans un thread séparé pour ne pas bloquer l'application principale. |

#### Usage

##### 1. Programmatic (dans un script Python)

Voici comment instancier et utiliser le `ConsoleHandler` directement dans votre code.

```python
from zpp_logs.core import Logger, CustomFormatter
from zpp_logs.handlers.console import ConsoleHandler
from zpp_logs.levels import INFO

# 1. Créer un formateur
formatter = CustomFormatter(
    format_str="{{ timestamp.strftime('%H:%M:%S') }} - {{ levelname }} - {{ msg }}"
)

# 2. Créer une instance du handler
console_handler = ConsoleHandler(level=INFO, formatter=formatter)

# 3. Créer un logger avec ce handler
logger = Logger(name="my_app", handlers=[console_handler])

# 4. Envoyer un message
logger.info("Ceci est un test pour la console.")
logger.debug("Ce message ne sera pas affiché car son niveau est inférieur à INFO.")
```

##### 2. Déclaratif (dans `config.yaml`)

Voici comment configurer le `ConsoleHandler` dans votre fichier `config.yaml`.

```yaml
# config.yaml

formatters:
  console_format:
    format: "{{ levelname }}: {{ msg }}"

handlers:
  # Nom de notre instance de handler
  console_out:
    # Classe à utiliser
    class: zpp_logs.ConsoleHandler
    # Options du handler
    level: INFO
    formatter: console_format
    output: sys.stdout

loggers:
  root:
    # Associer le handler au logger
    handlers: [console_out]
```


### DatabaseHandler

Le `DatabaseHandler` enregistre les messages de log dans une table de base de données relationnelle.

#### Fonctionnalité

Ce handler puissant utilise `SQLAlchemy` pour se connecter à différentes bases de données (SQLite et MySQL sont supportés nativement) et y insérer les enregistrements de log. Il offre une grande flexibilité pour structurer les données de log.

Il peut fonctionner de deux manières :
1.  **Mode Automatique :** Si vous ne fournissez pas de modèle SQLAlchemy, le handler créera automatiquement une table avec des colonnes par défaut (`id`, `timestamp`, `level`, `logger_name`, `message`) ou selon un mapping que vous spécifiez.
2.  **Mode Modèle :** Vous pouvez fournir votre propre classe de modèle SQLAlchemy. Le handler utilisera la table définie par ce modèle pour y insérer les logs.

**Dépendances :** Ce handler requiert `SQLAlchemy`. Pour MySQL, vous aurez également besoin de `PyMySQL` (`pip install sqlalchemy pymysql`).

#### Options

| Paramètre | Type | Défaut | Description |
|-----------|------|---------|-------------|
| `level` | `int` | `NOTSET` | Le niveau de log minimum requis. |
| `formatter`| `CustomFormatter`| `None` | Formateur (moins crucial ici car les données sont mappées, mais toujours utilisé pour les règles). |
| `connector` | `dict` | `None` | **Requis.** Dictionnaire de connexion à la base de données. |
| `columns` | `dict` | `None` | Optionnel. Mappe les noms de colonnes de la table aux expressions Jinja2 à extraire du log record. |
| `model` | `str` or `DeclarativeMeta`| `None`| Optionnel. Le modèle SQLAlchemy à utiliser (soit la classe, soit le chemin d'importation).|
| `ops` | `str` | `'>='` | Opérateur de comparaison pour le niveau. |
| `async_mode` | `bool` | `False` | Si `True`, l'insertion en base de données se fait dans un thread séparé. |

##### Détails du `connector`

Le dictionnaire `connector` doit contenir :
- `engine`: `'sqlite'` ou `'mysql'`.
- Pour SQLite : `filename` (chemin du fichier) et `table` (nom de la table).
- Pour MySQL : `host`, `user`, `password`, `database`.

##### Détails du `columns`

Ce dictionnaire est la clé de la flexibilité. La clé est le nom de la colonne dans la base de données, la valeur est une expression Jinja2.

Exemple : `{'user_id': 'user.id', 'request_path': 'request.path'}`

#### Usage

##### 1. Programmatic (Mode Automatique)

```python
from zpp_logs.core import Logger, CustomFormatter
from zpp_logs.handlers.database import DatabaseHandler
from zpp_logs.levels import INFO

# 1. Définir le connecteur pour une base SQLite
db_connector = {
    'engine': 'sqlite',
    'filename': 'logs/app_logs.db',
    'table': 'activity_logs'
}

# 2. Définir le mapping des colonnes
# On veut enregistrer le timestamp, le niveau, le message et un 'user_id' personnalisé
column_mapping = {
    'timestamp': 'timestamp',
    'level': 'levelname',
    'message': 'msg',
    'user_id': 'user_id' # 'user_id' sera passé en kwarg
}

# 3. Créer une instance du handler
db_handler = DatabaseHandler(
    level=INFO,
    formatter=CustomFormatter(""), # Le formateur est moins important ici
    connector=db_connector,
    columns=column_mapping
)

# 4. Créer un logger
logger = Logger(name="db_app", handlers=[db_handler])

# 5. Envoyer un log avec un champ personnalisé
logger.info("L'utilisateur a changé son mot de passe.", user_id=123)
logger.warning("Tentative de connexion échouée.", user_id=456)
```

##### 2. Déclaratif (dans `config.yaml`)

```yaml
# config.yaml

formatters:
  # Un formateur vide est suffisant, car le mapping se fait dans le handler
  db_format:
    format: ""

handlers:
  log_to_db:
    class: zpp_logs.DatabaseHandler
    level: INFO
    formatter: db_format
    # Configuration du connecteur
    connector:
      engine: sqlite
      filename: "config_logs.db"
      table: "system_events"
    # Configuration du mapping
    columns:
      timestamp: timestamp
      level: levelname
      message: msg
      logger: name

loggers:
  root:
    handlers: [log_to_db]
```

### FileHandler

Le `FileHandler` écrit les messages de log dans un fichier sur le système de fichiers.

#### Fonctionnalité

Ce handler est utilisé pour la persistance des logs. Il écrit les messages formatés dans un fichier spécifié. Il supporte également des fonctionnalités avancées comme la rotation de fichiers (log rotation) basée sur la taille, ce qui permet de gérer l'espace disque utilisé par les logs.

- **Rotation Standard :** Quand la taille maximale est atteinte, le fichier de log actuel est renommé (ex: `app.log` -> `app.log.1`) et un nouveau fichier vide est créé.
- **Rotation Circulaire :** Un mode spécial où, au lieu de créer de nouveaux fichiers, la ligne la plus ancienne du fichier est supprimée pour faire de la place.

#### Options

| Paramètre | Type | Défaut | Description |
|-----------|------|---------|-------------|
| `level` | `int` | `NOTSET` | Le niveau de log minimum requis. |
| `formatter`| `CustomFormatter`| `None` | L'instance `CustomFormatter` pour la mise en forme. |
| `filters` | `list` | `None` | Filtres Jinja2 pour un contrôle fin. |
| `filename` | `str` | `None` | **Requis.** Le chemin vers le fichier de log. Peut inclure des variables Jinja2. |
| `maxBytes` | `int` | `0` | La taille maximale en octets que le fichier de log peut atteindre avant la rotation. Si `0`, la rotation est désactivée. |
| `backupCount`| `int` | `0` | Le nombre de fichiers de sauvegarde à conserver. Si `> 0`, la rotation standard est utilisée. Si `0` et `maxBytes > 0`, la rotation circulaire est utilisée. |
| `ops` | `str` | `'>='` | L'opérateur de comparaison pour le niveau. |
| `async_mode` | `bool` | `False` | Si `True`, l'écriture des logs se fait dans un thread séparé. |

#### Usage

##### 1. Programmatic (dans un script Python)

Voici comment configurer un `FileHandler` avec rotation.

```python
from zpp_logs.core import Logger, CustomFormatter
from zpp_logs.handlers.file import FileHandler
from zpp_logs.levels import DEBUG

# 1. Créer un formateur détaillé
formatter = CustomFormatter(
    format_str="{{ timestamp.isoformat() }} | {{ levelname }} | {{ msg }}"
)

# 2. Créer une instance du handler avec rotation
# Rotation après 1 MB, conserve 3 fichiers de backup (app.log.1, app.log.2, app.log.3)
file_handler = FileHandler(
    level=DEBUG,
    formatter=formatter,
    filename='app.log',
    maxBytes=1024 * 1024,  # 1 MB
    backupCount=3
)

# 3. Créer un logger avec ce handler
logger = Logger(name="file_app", handlers=[file_handler])

# 4. Envoyer des messages
logger.info("L'application a démarré.")
logger.debug("Ceci est une information de diagnostic.")
```

##### 2. Déclaratif (dans `config.yaml`)

Voici comment configurer le `FileHandler` dans votre fichier `config.yaml`.

```yaml
# config.yaml

formatters:
  file_format:
    format: "{{ timestamp }} | {{ name }} | {{ levelname }} | {{ msg }}"

handlers:
  # Nom de notre instance de handler
  log_to_file:
    # Classe à utiliser
    class: zpp_logs.FileHandler
    # Options du handler
    level: DEBUG
    formatter: file_format
    filename: config_app.log
    maxBytes: 512000  # 500 KB
    backupCount: 5
    encoding: utf-8

loggers:
  root:
    handlers: [log_to_file]
```


### ResendHandler

Le `ResendHandler` envoie des emails de log en utilisant l'API du service [Resend](https://resend.com).

#### Fonctionnalité

Ce handler est une alternative moderne au `SMTPHandler`. Il s'intègre avec Resend, une plateforme d'envoi d'emails transactionnels pour les développeurs. Il est idéal pour envoyer des alertes critiques de manière fiable sans avoir à gérer son propre serveur SMTP.

Le handler envoie une requête POST à l'API de Resend. Le sujet de l'email peut être un template Jinja2, et le corps de l'email (`html`) est le message brut (`msg`) du log.

**Dépendances :** Ce handler requiert la librairie `requests` (`pip install requests`).

#### Options


| Paramètre     | Type              | Défaut   | Description                                                                                                    |
| ------------- | ----------------- | -------- | -------------------------------------------------------------------------------------------------------------- |
| `level`       | `int`             | `NOTSET` | Le niveau de log minimum (ex: `ERROR`).                                                                        |
| `formatter`   | `CustomFormatter` | `None`   | Formateur (le corps de l'email est `msg` brut, mais le formateur peut être utile pour les règles et le sujet). |
| `host`        | `str`             | `None`   | **Requis.** L'adresse du serveur SMTP.                                                                         |
| `port`        | `int`             | `None`   | **Requis.** Le port du serveur SMTP (ex: 587 pour TLS).                                                        |
| `username`    | `str`             | `None`   | **Requis.** Le nom d'utilisateur pour s'authentifier auprès du serveur SMTP.                                   |
| `password`    | `str`             | `None`   | **Requis.** Le mot de passe pour l'authentification.                                                           |
| `fromaddr`    | `str`             | `None`   | **Requis.** L'adresse email de l'expéditeur.                                                                   |
| `toaddrs`     | `list`            | `None`   | **Requis.** Une liste d'adresses email de destinataires.                                                       |
| `subject`     | `str`             | `None`   | **Requis.** Le sujet de l'email. Peut contenir des expressions Jinja2.                                         |
| `ops`         | `str`             | `'>='`   | L'opérateur de comparaison pour le niveau.                                                                     |
| `async_mode`  | `bool`            | `False`  | Si `True`, l'envoi de l'email se fait dans un thread séparé pour ne pas bloquer l'application.                 |
| `insecure`    | `bool`            | `False`  | Si `True`, connexion au serveur sans TLS                                                                       |
| `cc`          | `list`            | `None`   | Personne en copie des mails                                                                                    |
| `bcc`         | `list`            | `None`   | Personne en copie des mails                                                                                    |
| `attachments` | `list`            | `None`   | Listes des fichiers à joindre au mail                                                                          |

#### Usage

##### 1. Programmatic (dans un script Python)

**Note :** Ne jamais coder en dur votre clé d'API. Utilisez des variables d'environnement.

```python
import os
from zpp_logs.core import Logger, CustomFormatter
from zpp_logs.handlers.resend import ResendHandler
from zpp_logs.levels import ERROR

# 1. Créer une instance du handler
# La clé d'API est récupérée depuis les variables d'environnement
resend_handler = ResendHandler(
    level=ERROR,
    formatter=CustomFormatter(""), # Corps de l'email = msg
    api_key=os.environ.get('RESEND_API_KEY'),
    fromaddr="onboarding@resend.dev", # Adresse d'exemple fournie par Resend
    to=["votre_email@exemple.com"],
    subject="[ERREUR] Un problème est survenu sur {{ name }}"
)

# 2. Créer un logger avec ce handler
logger = Logger(name="user_service", handlers=[resend_handler])

# 3. Envoyer un log qui déclenchera l'email via Resend
logger.error("Impossible de mettre à jour le profil de l'utilisateur #500. Erreur de base de données.")
```

##### 2. Déclaratif (dans `config.yaml`)

**Attention :** Stocker des clés d'API en clair dans des fichiers de configuration est une mauvaise pratique.

```yaml
# config.yaml

formatters:
  resend_format:
    format: ""

handlers:
  send_resend_alert:
    class: zpp_logs.ResendHandler
    level: ERROR
    formatter: resend_format
    # --- Paramètres Resend ---
    # Idéalement, utilisez un placeholder qui est remplacé au démarrage de l'app
    api_key: "RE_VOTRE_CLÉ_API_Ici"
    fromaddr: "app@votre-domaine-verifie.com"
    to:
      - "devops@exemple.com"
    subject: "Erreur détectée dans le service {{ name }}"

loggers:
  user_service: # Logger spécifique
    handlers: [send_resend_alert]
  root: # Logger racine
    handlers: [] # Ne pas envoyer d'email pour les logs généraux
```

### SMTPHandler

Le `SMTPHandler` envoie les messages de log par email via un serveur SMTP.

#### Fonctionnalité

Ce handler est particulièrement utile pour les notifications d'événements critiques. Lorsqu'un log atteint un certain niveau de sévérité (typiquement `ERROR` ou `CRITICAL`), ce handler peut envoyer un email à une liste de destinataires pour une alerte immédiate.

Le sujet de l'email peut être une chaîne de caractères formatée avec Jinja2, permettant de créer des sujets dynamiques. Le corps de l'email est le message brut du log (`msg`). La connexion au serveur SMTP se fait via TLS pour plus de sécurité.

#### Options

| Paramètre | Type | Défaut | Description |
|-----------|------|---------|-------------|
| `level` | `int` | `NOTSET` | Le niveau de log minimum (ex: `ERROR`). |
| `formatter`| `CustomFormatter`| `None` | Formateur (le corps de l'email est `msg` brut, mais le formateur peut être utile pour les règles et le sujet). |
| `host` | `str` | `None` | **Requis.** L'adresse du serveur SMTP. |
| `port` | `int` | `None` | **Requis.** Le port du serveur SMTP (ex: 587 pour TLS). |
| `username` | `str` | `None` | **Requis.** Le nom d'utilisateur pour s'authentifier auprès du serveur SMTP. |
| `password` | `str` | `None` | **Requis.** Le mot de passe pour l'authentification. |
| `fromaddr` | `str` | `None` | **Requis.** L'adresse email de l'expéditeur. |
| `toaddrs` | `list` | `None` | **Requis.** Une liste d'adresses email de destinataires. |
| `subject` | `str` | `None` | **Requis.** Le sujet de l'email. Peut contenir des expressions Jinja2. |
| `ops` | `str` | `'>='` | L'opérateur de comparaison pour le niveau. |
| `async_mode` | `bool` | `False` | Si `True`, l'envoi de l'email se fait dans un thread séparé pour ne pas bloquer l'application. |

#### Usage

##### 1. Programmatic (dans un script Python)

**Note :** Pour des raisons de sécurité, évitez de coder en dur les identifiants. Utilisez des variables d'environnement ou un gestionnaire de secrets.

```python
import os
from zpp_logs.core import Logger, CustomFormatter
from zpp_logs.handlers.smtp import SMTPHandler
from zpp_logs.levels import CRITICAL

# 1. Créer une instance du handler avec les informations du serveur SMTP
# (Ici, nous supposons que les identifiants sont dans des variables d'environnement)
smtp_handler = SMTPHandler(
    level=CRITICAL,
    formatter=CustomFormatter(""), # Le corps est le message brut
    host="smtp.exemple.com",
    port=587,
    username=os.environ.get('SMTP_USER'),
    password=os.environ.get('SMTP_PASS'),
    fromaddr="noreply@monapp.com",
    toaddrs=["admin@exemple.com", "dev-on-call@exemple.com"],
    subject="[ALERTE CRITIQUE] Erreur dans {{ name }}"
)

# 2. Créer un logger avec ce handler
logger = Logger(name="payment_gateway", handlers=[smtp_handler])

# 3. Envoyer un log critique qui déclenchera l'envoi d'un email
logger.critical("Échec du traitement du paiement pour la transaction #12345.")
```

##### 2. Déclaratif (dans `config.yaml`)

**Attention :** Stocker des mots de passe en clair dans des fichiers de configuration est une mauvaise pratique de sécurité. Préférez des mécanismes d'injection de secrets. Cet exemple est à titre illustratif.

```yaml
# config.yaml

formatters:
  email_format:
    format: "" # Non utilisé pour le corps de l'email

handlers:
  send_alert_email:
    class: zpp_logs.SMTPHandler
    level: CRITICAL
    formatter: email_format
    # --- Paramètres SMTP ---
    host: smtp.exemple.com
    port: 587
    # Idéalement, utilisez des 'placeholders' que vous remplacez au démarrage
    username: "MON_USER_SMTP"
    password: "MON_MOT_DE_PASSE_SMTP"
    fromaddr: "alert@system.com"
    toaddrs:
      - "admin-equipe-a@exemple.com"
      - "admin-equipe-b@exemple.com"
    subject: "ALERTE: {{ levelname }} dans le logger '{{ name }}'"

loggers:
  root:
    handlers: [send_alert_email] # Attacher le handler au logger
```


### WebhookHandler

Le `WebhookHandler` envoie les messages de log à une URL de webhook via une requête HTTP POST.

#### Fonctionnalité

Ce handler est extrêmement versatile et permet de s'intégrer avec une multitude de services tiers (Slack, Discord, IFTTT, Zapier, etc.) ou avec vos propres endpoints d'API. Il envoie une charge utile (payload) JSON personnalisable à une URL spécifiée.

Il supporte plusieurs méthodes d'authentification pour sécuriser les appels :
- **Bearer Token :** Authentification via un jeton dans l'en-tête `Authorization`.
- **Basic Auth :** Authentification HTTP Basic avec un nom d'utilisateur et un mot de passe.
- **Custom Token :** Authentification via un jeton secret passé dans l'en-tête `X-Webhook-Token`.
- **Aucune :** Si aucune méthode n'est spécifiée, la requête est envoyée sans authentification.

**Dépendances :** Ce handler requiert la librairie `requests` (`pip install requests`).

#### Options

| Paramètre | Type | Défaut | Description |
|-----------|------|---------|-------------|
| `level` | `int` | `NOTSET` | Le niveau de log minimum requis pour déclencher l'envoi. |
| `formatter`| `CustomFormatter`| `None` | Formateur (utile pour les règles, moins pour le formatage direct). |
| `url` | `str` | `None` | **Requis.** L'URL du webhook à appeler. |
| `data` | `dict` | `{}` | **Requis.** Un dictionnaire définissant la structure du JSON à envoyer. Les valeurs sont des templates Jinja2. |
| `bearer` | `str` | `None` | Le jeton (token) à utiliser pour l'authentification de type "Bearer". |
| `basic` | `dict` | `None` | Un dictionnaire avec les clés `user` and `pass` pour l'authentification "Basic". |
| `token` | `str` | `None` | Le jeton à passer dans l'en-tête `X-Webhook-Token` pour une authentification personnalisée. |
| `ssl_verify`|`bool` | `True` | Si `False`, la vérification du certificat SSL de l'URL du webhook sera désactivée. À utiliser avec prudence. |
| `ops` | `str` | `'>='` | L'opérateur de comparaison pour le niveau. |
| `async_mode` | `bool` | `False` | Si `True`, l'appel au webhook se fait dans un thread séparé. |

#### Usage

##### 1. Programmatic (dans un script Python)

```python
import os
from zpp_logs.core import Logger, CustomFormatter
from zpp_logs.handlers.webhook import WebhookHandler
from zpp_logs.levels import WARNING

# 1. Définir la structure de la charge utile (payload)
json_payload_template = {
    "content": "Alerte de niveau {{ levelname }} sur le service {{ name }}",
    "embeds": [{
        "title": "Détails du Log",
        "description": "{{ msg }}",
        "color": 16711680 # Rouge pour les erreurs (exemple pour Discord)
    }],
    "extra_data": {
        "request_id": "{{ request_id | default('N/A') }}"
    }
}

# 2. Créer une instance du handler
webhook_handler = WebhookHandler(
    level=WARNING,
    formatter=CustomFormatter(""), # Pas besoin de formateur de chaîne ici
    url=os.environ.get("DISCORD_WEBHOOK_URL"),
    data=json_payload_template
    # Aucune authentification nécessaire pour les webhooks Discord
)

# 3. Créer un logger avec ce handler
logger = Logger(name="api_gateway", handlers=[webhook_handler])

# 4. Envoyer un log
logger.warning(
    "Le temps de réponse de l'API externe a dépassé le seuil.",
    request_id="a7b2c9x4"
)
```

##### 2. Déclaratif (dans `config.yaml`)

C'est ici que ce handler brille par sa lisibilité.

######## Exemple 1 : Authentification Bearer

```yaml
formatters:
  standard: # Le formateur peut être vide si non nécessaire
    format: ""

handlers:
  send_to_my_api:
    class: zpp_logs.WebhookHandler
    level: INFO
    formatter: standard
    url: "https://api.mon-service.com/v1/log"
    # --- Authentification ---
    bearer: "VOTRE_JETON_API_SECRET"
    # --- Données JSON ---
    data:
      application: "backend-worker"
      source: "production"
      status: "{{ levelname }}"
      message: "{{ msg }}"
      user_context: "{{ user_id | default('system') }}"

loggers:
  root:
    handlers: [send_to_my_api]
```

######## Exemple 2 : Authentification Basic

```yaml
handlers:
  send_to_legacy_system:
    class: zpp_logs.WebhookHandler
    level: ERROR
    formatter: standard
    url: "https://legacy.interne/api/log"
    # --- Authentification ---
    basic:
      user: "api_user"
      pass: "S3cr3tP4ssw0rd"
    # --- Données JSON ---
    data:
      severity: "{{ levelno }}"
      text: "{{ msg }}"

loggers:
  legacy_connector:
    handlers: [send_to_legacy_system]
```

######## Exemple 3 : Authentification par Jeton Personnalisé (`X-Webhook-Token`)

```yaml
handlers:
  send_to_private_webhook:
    class: zpp_logs.WebhookHandler
    level: INFO
    formatter: standard
    url: "https://mon-service.privé/webhook"
    # --- Authentification ---
    token: "VOTRE_TOKEN_SECRET_PARTAGÉ"
    # --- Données JSON ---
    data:
      source: "{{ name }}"
      log_level: "{{ levelname }}"
      log_message: "{{ msg }}"

loggers:
  private_app:
    handlers: [send_to_private_webhook]
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
