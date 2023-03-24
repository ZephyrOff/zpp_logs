# zpp-logs
## Informations
Module pour la gestion des logs (à l'image de logging) avec des tuning personnalisés par niveau de logs
<br>

## Prérequis
- Python 3
<br>

## Installation
```console
pip install zpp-logs
```
<br>

## Utilisation
### <ins>Logger</ins>

Un logger est un objet qui permet de définir des options (handler, formatter, filter) pour un log.

```python
from zpp_logs import Logger

log = Logger()
```
<br>
Il est possible de lui donner en paramètre un fichier de configuration au format yaml pour configurer directement les différentes options

```python
from zpp_logs import Logger

log = Logger(configfile='config.yaml')
```

_Exemple de fichier yaml:_
```config
formatters:
    standard:
        format: "%(fore:deep_sky_blue_3a)%[%(date:%d/%m/%Y %H:%M:%S)%]%(attr:0)% - %(fore:medium_purple_4)%%(levelname)%%(attr:0)% - %(fore:grey_46)%%(msg)%%(attr:0)%"
    test:
        format: "%(epoch)% - %(msg)%"

filters:
    testfunc: test3.test

handlers:
    console:
        class: zpp_logs.Console_handler
        level: zpp_logs.CRITICAL
        ops: "<"
        formatter: test
        output: sys.stdout


logger:
    handlers: [console]
    filters: [testfunc]
```

<br>

Dans un Logger, nous pouvons ajouter/supprimer des handler et des filtres, afficher le compteur de log et appeler les méthodes de log.
Toutes ces options sont détaillées dans la suite.

<br>

### <ins>Handler</ins>

Différents handler sont disponibles pour permettre d'envoyer les logs dans la console, dans un fichier ou par mail.
Tous les handler disposent des méthodes:
- __setFormatter()__ pour ajouter un formatter
```python
cons.setFormatter(form)
```
la méthode attend un objet Formatter

<br>

- __setLevel()__ pour définir le niveau de log à appliquer
```python
cons.setLevel(zpp_logs.DEBUG)
```
la méthode attend un niveau de logs.
Il est possible de lui envoyer un argument ops pour définir le comportement du handler. (Par défaut ==)
```python
cons.setLevel(zpp_logs.ERROR, ops="<=")
```
le ops permet de comparaison pour trigger le handler. Dans l'exemple du dessus, le handler se déclenche si le log est de niveau ERROR ou inférieur.

<br>

- __addFilter()__ pour ajouter un filtre.
Le filter est soit un script (qui peut être une regex), soit une fonction (dans ce cas, le filter attends un retour True pour se déclencer)
```python
def test(message):
    if "bjr" in message:
        return True
    return False

cons.addFilter(MonModule.test)
```

<br>

- __removeFilter()__ pour supprimer un filtre.
Cette méthode permet de supprimer un filtre configuré

<br>

### Console_handler

Un Console_handler permet d'envoyer des messages dans la console.
Par défaut, le handler n'attend pas de paramètre mais peut recevoir:
- output: pour définir la destination (Par défaut sys.stdout)
- level: pour définir le niveau de logs attendu (Par défaut NOTSET)
- ops: pour définir le comportement du handler. (Par défaut ==) (Voir setLevel)

```python
log = Logger()
cons = Console_handler()
log.add_handler(cons)
```

<br>

### File_handler

Un File_handler permet d'envoyer des messages dans un fichier.
Par défaut, le handler attend le chemin du fichier de destination. (Peut recevoir un nom de fichier dynamique avec la syntaxe des formatter) <br>
Il peut aussi recevoir:
- rewrite: pour définir si le handler réécrit sur un fichier existant (Par défaut False)
- level: pour définir le niveau de logs attendu (Par défaut NOTSET)
- ops: pour définir le comportement du handler. (Par défaut ==) (Voir setLevel)

```python
log = Logger()
cons = File_handler('content.log')
log.add_handler(cons)
```

<br>

### RotateFile_handler

Un RotateFile_handler permet d'envoyer des messages dans un fichier en prenant en charge une rotation de logs en fonction d'une taille max.
Par défaut, le handler attend le chemin du fichier de destination. (Peut recevoir un nom de fichier dynamique avec la syntaxe des formatter) <br>
Il peut aussi recevoir:
- rewrite: pour définir si le handler réécrit sur un fichier existant (Par défaut False)
- level: pour définir le niveau de logs attendu (Par défaut NOTSET)
- ops: pour définir le comportement du handler. (Par défaut ==) (Voir setLevel)
- maxBytes: pour définir la taille max du fichier de log
- backupCount: pour définir le nombre maximum de fichier de log. Si la limite est atteinte, il supprime le fichier le plus ancien.

```python
log = Logger()
cons = RotateFile_handler('content.log')
log.add_handler(cons)
```

<br>

### SMTP_handler

Un SMTP_handler permet d'envoyer des messages par mail.
Par défaut, le handler attend les paramètres:
- smtphost: l'ip ou l'adresse du serveur SMTP sous forme de str. Possibilité de lui envoyer un tuple pour définir le port à utiliser (HOST, PORT)
- fromaddr: l'adresse mail de l'expéditeur sous forme de str
- toaddrs: la/les adresses mail des destinataires sous forme de str pour un destination ou une liste pour plusieurs 
- subject: l'objet du mail (Peut recevoir un objet dynamique avec la syntaxe des formatter)
<br>

Il peut aussi recevoir:
- credentials: pour définir les login de connexion sous forme de liste ou tuple (USERNAME, PASSWORD)
- secure: pour définir si la connexion doit être sécurisée (Par défaut None)
- timeout: pour définir le temps timeout pour la réponse du serveur SMTP (Par défaut 5.0)
- level: pour définir le niveau de logs attendu (Par défaut NOTSET)
- ops: pour définir le comportement du handler. (Par défaut ==) (Voir setLevel)

```python
log = Logger()
cons = SMTP_handler(smtphost='smtp.local.com', fromaddr='private@local.com', toaddrs=['user1@gmail.com', 'user2@gmail.com'], subject="Test de notification")
log.add_handler(cons)
```

<br>

### <ins>Formatter</ins>

Un formatter est un objet qui permet de définir le format du message de log envoyé
Dans un formatter, les trigger doivent être de la forme _%(trigger_name)%_
Si on veut formater un peu de texte pour aligner les logs, on peut définir un padding en ajoutant la taille avec le 2ème %
Par exemple, _%(trigger_name)5%_

Voici la liste des trigger disponibles

| Name | Description |
|----------|-------------|
| asctime | Date au format %d/%m/%Y %H:%M:%S:%f |
| date: strftime_format | Date dans le format qu'on veut |
| epoch | Date au format epoch |
| exc_info			 | Récupération du traceback |
| levelname | Nom du niveau de log |
| levelno			 | ID du niveau de log |
| msg | Message de log |
| filename | Nom du fichier d'exécution |
| filepath | Répertoire parent du fichier d'exécution |
| lineno | Numéro de la ligne du fichier d'exécution |
| functname | Nom de la fonction |
| path | Chemin actuel |
| process | Nom du process |
| processid | PID du process |
| username | Nom d'utilisateur qui exécute le script |
| uid | uid de l'utilisateur qui exécute le script (only linux) |
| os_name | Nom de l'OS |
| os_version | Version de l'OS |
| os_archi | Architecture de l'OS |
| mem_total | Capacité max de RAM |
| mem_available | Capacité disponible de RAM |
| mem_used | Capacité utilisée de RAM |
| mem_free | Capacité disponible de RAM |
| mem_percent | Capacité utilisée de RAM en pourcentage |
| swap_total | Capacité max de Swap |
| swap_used | Capacité utilisée de Swap |
| swap_free | Capacité disponible de Swap |
| swap_percent | Capacité utilisée de Swap en pourcentage |
| cpu_count | Nombre de core physique |
| cpu_logical_count | Nombre de core logique |
| cpu_percent | Pourcentage de CPU utilisé |
| current_disk_device | Nom du disque où se trouve le script |
| current_disk_mountpoint | Point de montage du disque où se trouve le script |
| current_disk_fstype | Format du disque où se trouve le script |
| current_disk_total | Capacité max du disque où se trouve le script |
| current_disk_used | Capacité utilisée du disque où se trouve le script |
| current_disk_free | Capacité disponible du disque où se trouve le script |
| current_disk_percent | Capacité utilisée en pourcentage du disque où se trouve le script |
| fore: color | Couleur de la police d'écriture |
| back: color | Couleur du fond de la police d'écriture |
| attr: attribute | Style de la police d'écriture |

<br>
Pour son utilisation, il suffit de créer un objet Formatter et de l'ajouter dans un handler.

```python
from zpp_logs import Logger, Formatter, Console_handler

log = Logger()
form = Formatter("%(fore:deep_sky_blue_3a)%[%(date:%d/%m/%Y %H:%M:%S)%]%(attr:0)% - %(fore:medium_purple_4)%%(levelname)%%(attr:0)% - %(fore:grey_46)%%(msg)%%(attr:0)%")
cons = Console_handler()
cons.setFormatter(form)
```

<br>

### <ins>Envoi des logs</ins>

Les méthodes pour envoyer des logs se déclinent en 7 niveaux: 
- log(message): zpp_logs.NOTSET
- good(message): zpp_logs.GOOD
- debug(message): zpp_logs.DEBUG
- info(message): zpp_logs.INFO
- warning(message): zpp_logs.WARNING
- error(message): zpp_logs.ERROR
- critical(message): zpp_logs.CRITICAL

<br>

Ces méthodes peuvent être appelées soit en direct, soit depuis un logger.
```python
from zpp_logs import Logger

logger = Logger(configfile="config.yaml")
logger.warning("Test de logs")
```
<br> 

### <ins>Compteur des logs</ins>

Il est possible de récupérer un dictionnaire contenant le compteur des logs envoyés par un logger.
```python
>>> logger.count()
{'CRITICAL': 0, 'ERROR': 0, 'WARNING': 1, 'INFO': 0, 'GOOD': 0, 'DEBUG': 0, 'NOTSET': 0}
```