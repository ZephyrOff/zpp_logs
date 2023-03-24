import impmagic

reg_foreground = r"fore:(?P<color>\w+)"
reg_background = r"back:(?P<color>\w+)"
reg_attribute = r"attr:(?P<color>\w+)"
reg_date = r"date:(?P<date_format>[^)]*)"
reg_action = r"%\((?P<action>[^)]*)\){1}(?P<padding>\d*)%"

NOTSET = 0
DEBUG = 10
GOOD = 15
INFO = 20
WARNING = 30
ERROR = 40
CRITICAL = 50

_levelToName = {
	CRITICAL: 'CRITICAL',
	ERROR: 'ERROR',
	WARNING: 'WARNING',
	INFO: 'INFO',
	GOOD: 'GOOD',
	DEBUG: 'DEBUG',
	NOTSET: 'NOTSET',
}

_nameToLevel = {
	'CRITICAL': CRITICAL,
	'ERROR': ERROR,
	'WARNING': WARNING,
	'INFO': INFO,
	'GOOD': GOOD,
	'DEBUG': DEBUG,
	'NOTSET': NOTSET,
}



def sizeconvert(size):
	size = int(size)
	if size < 1024:
	  return str(round(size / 1024.0)) + " Octets"
	elif size < 1024**2:
	  return str(round(size / 1024.0, 3)) + " Ko"
	elif size < 1024**3:
	  return str(round(size / (1024.0**2), 2)) + " Mo"
	else:
	  return str(round(size / (1024.0**3), 2)) + " Go"

@impmagic.loader(
    {'module': 'psutil'}
)
def list_disk():
	array = []
	for element in psutil.disk_partitions(all=True):
		if "cdrom" in element.opts:
			if element.fstype!="":
				info = psutil.disk_usage(element.device)
				array.append({"device": element.device, "mountpoint": element.mountpoint, "fstype": element.fstype, "total_size": sizeconvert(info.total), "used_size": sizeconvert(info.used), "free_size": sizeconvert(info.free), "percent": info.percent})

		else:
			info = psutil.disk_usage(element.device)
			array.append({"device": element.device, "mountpoint": element.mountpoint, "fstype": element.fstype, "total_size": sizeconvert(info.total), "used_size": sizeconvert(info.used), "free_size": sizeconvert(info.free), "percent": info.percent})

	return array

def get_disk_info(mountpoint):
	for disk in list_disk():
		if mountpoint.startswith(disk['mountpoint']):
			return disk

def compare_level(handler_level, operator, level):
	if operator==">=" and level>=handler_level:
		return True
	elif operator=="!=" and level!=handler_level:
		return True
	elif operator=="<" and level<handler_level:
		return True
	elif operator==">" and level>handler_level:
		return True
	elif operator=="<=" and level<=handler_level:
		return True
	elif operator=="==" and level==handler_level:
		return True
	return False

@impmagic.loader(
    {'module': '__main__'},
    {'module': 'os.path','submodule': ['split', 'abspath', 'join']}
)
def split_path():
    if split(__file__)[0]=="":
        return join(abspath('.'))
    else:
        return join(split(__file__)[0])

@impmagic.loader(
	{'module': 'os.path', 'submodule':['isabs', 'abspath', 'join']}
)
def path_reg(arg):
	if isabs(arg):
		return arg
	return join(split_path(), arg)


class Logger:
	@impmagic.loader(
        {'module': 'yaml'},
        {'module': 'inspect'},
        {'module': 'os.path','submodule': ['abspath', 'exists', 'isfile']}
    )
	def __init__(self, configfile = None):
		self.__handlers = []
		self.__count = {
			'CRITICAL': 0,
			'ERROR': 0,
			'WARNING': 0,
			'INFO': 0,
			'GOOD': 0,
			'DEBUG': 0,
			'NOTSET': 0,
		}

		#Liste des paramètres qui pourront être convertis en module
		trigger = ["class", "level", "output", "formatter", "secure", "timeout", "stream"]
		if configfile:
			configfile = path_reg(configfile)
			if exists(configfile) and isfile(configfile):
				with open(configfile, 'rt') as f:
					try:
						config = yaml.safe_load(f.read())
						if config!=None and "formatters" in config.keys() and "handlers" in config.keys() and "logger" in config.keys():
							config_formatter = {}

							logger = config['logger']
							if logger!=None and "handlers" in logger.keys():
								handlers = logger['handlers']
								if handlers!=None:
									#Charge les handlers s'ils sont dans le logger
									for handler_logger in handlers:
										if handler_logger in config['handlers']:
											handler = config['handlers'][handler_logger]
											if handler!=None and "class" in handler.keys() and "formatter" in handler.keys():
												class_hand = impmagic.get(handler['class'])
												if class_hand!=None:
													#Parce le fichier de conf et génère le dictionnaire des arguments en fonction des paramètres obligatoires
													signature = inspect.signature(class_hand)

													args = {}
													for name, param in signature.parameters.items():
														setted = False
														if name=="credentials":
															if "user" in handler.keys() and "password" in handler.keys():
																args['credentials'] = (handler['user'], handler['password'])
																setted = True
														elif name=="ops":
															if "ops" in handler and (handler['ops']==">=" or handler['ops']=="!=" or handler['ops']=="<" or handler['ops']==">" or handler['ops']=="<=" or handler['ops']=="=="):
																args['ops'] = handler['ops']
																setted = True
														else:
															if name in handler.keys():
																#Convertis le string en object si besoin
																if name in trigger and isinstance(handler[name], str) and "." in handler[name]: 
																	handler_param = impmagic.get(handler[name])
																	if handler_param!=None:
																		args[name] = handler_param
																	else:
																		args[name] = handler[name]
																else:
																	args[name] = handler[name]
																setted = True

														#Vérifie si le paramètre obligatoire a été initialisé
														if not setted and param.default==inspect.Parameter.empty:
															print(f"Class {handler['class']}: Missing {name} parameter")
															return

													#Création de la classe handler
													handler_called = class_hand(**args)

													#Ajout du formatter
													if handler['formatter'] in config_formatter:
														handler_called.setFormatter(config_formatter[handler['formatter']])
													else:
														if handler['formatter'] in config['formatters']:
															formname = handler['formatter']
															formatter = config['formatters'][formname]
															if isinstance(formatter, dict) and "format" in formatter.keys() and isinstance(formatter['format'], str):
																config_formatter[formname] = Formatter(formatter['format'])
																handler_called.setFormatter(config_formatter[formname])

													#Regarde s'il y a des filtres et les ajoutent au handler
													if "filters" in handler and 'filters' in config.keys() and config['filters']!=None:
														filters = config['filters']
														for fil in handler['filters']:
															if fil in filters:
																filter_conf = impmagic.get(filters[fil])
																if filter_conf!=None:
																	handler_called.addFilter(filter_conf)
																else:
																	handler_called.addFilter(filters[fil])

													#Ajoute le handler
													self.add_handler(handler_called)
											else:
												print(f"Handler {handler_logger}: Bad configuration")
										else:
											print(f"Handler {handler_logger} not found")

									#Regarde s'il y a des filtres et les ajoutent au logger
									if len(self.__handlers) and "filters" in logger.keys() and 'filters' in config.keys() and config['filters']!=None:
										filters = config['filters']
										for fil in logger['filters']:
											if fil in filters:
												filter_conf = impmagic.get(filters[fil])
												if filter_conf!=None:
													self.addFilter(filter_conf)
												else:
													self.addFilter(filters[fil])

								else:
									print("Handlers not configured")
							else:
								print("Handlers not configured in logger")

					except Exception as e:
						print(f"{e}")
						return

	def add_handler(self, handler):
		if hasattr(handler, "write"):
			self.__handlers.append(handler)	

	def remove_handler(self, handler):
		if handler in self.__handlers:
			self.__handlers.remove(handler)

	def addFilter(self, filter):
		for handler in self.__handlers:
			handler.addFilter(filter)

	def removeFilter(self, filter):
		for handler in self.__handlers:
			handler.removeFilter(filter)

	def write(self, message, level=0):
		if len(self.__handlers):
			if level in _levelToName:
				name = _levelToName.get(level)
				self.__count[name]+=1

			for handler in self.__handlers:
				handler.write(message, level)

	def count(self):
		return self.__count

	def log(self, message):
		self.write(message)
	def good(self, message):
		self.write(message, GOOD)
	def debug(self, message):
		self.write(message, DEBUG)
	def info(self, message):
		self.write(message, INFO)
	def warning(self, message):
		self.write(message, WARNING)
	def error(self, message):
		self.write(message, ERROR)
	def critical(self, message):
		self.write(message, CRITICAL)


##### SET FORMATTER #####
class Formatter:
	def __init__(self, pattern):
		self.pattern = pattern

	@impmagic.loader(
        {'module': 'sys'},
        {'module': 're'},
        {'module': 'os'},
        {'module': 'inspect'},
        {'module': 'psutil'},
        {'module': 'platform'},
        {'module': 'os','submodule': ['name'], 'as': 'osname'},
        {'module': 'os.path','submodule': ['abspath', 'dirname']},
        {'module': 'datetime','submodule': ['datetime']},
        {'module': 'zpp_color','submodule': ['fg', 'bg', 'attr']}
    )
	def get(self, message, level):
		result = self.pattern

		#Parse les arguments du formatter et remplace les trigger format si besoin
		for res in re.finditer(reg_action,result):
			insert=None

			if "asctime" == res.group("action"):
				date_now = datetime.now().strftime("%d/%m/%Y %H:%M:%S:%f")
				insert = date_now

			if re.findall(reg_date, res.group("action")):
				for rest in re.finditer(reg_date,res.group("action")):
					date_now = datetime.now().strftime(rest.group("date_format"))
					result = result.replace(res.group(), date_now)

			if "epoch" == res.group("action"):
				epoch = (datetime.now() - datetime(1970, 1, 1)).total_seconds()
				insert =  str(epoch)

			if "exc_info" == res.group("action"):
				insert =  sys.exc_info()
			
			if "levelname" == res.group("action"):
				insert = _levelToName.get(level,"")

			if "levelno" == res.group("action"):
				insert = str(level)
			
			if "msg" == res.group("action"):
				insert = message

			if "filename" == res.group("action") or "lineno" == res.group("action") or "functname" == res.group("action") or "filepath" == res.group("action"):
				stack = inspect.stack()

				if "filename" == res.group("action"):
					insert = stack[-1].filename
				if "lineno" == res.group("action"):
					insert = stack[-1].lineno
				if "functname" == res.group("action"):
					if stack[-1].filename==stack[-2].filename:
						insert = stack[-2].function
					else:
						insert = stack[-1].function
				if "filepath" == res.group("action"):
					insert = dirname(stack[-1].filename)

			if "path" == res.group("action"):
				insert = abspath(os.getcwd())
			
			if "process" == res.group("action"):
				insert = psutil.Process().name()
			if "processid" == res.group("action"):
				insert = str(psutil.Process().pid)

			if "username" == res.group("action"):
				insert = os.getlogin()
			if "uid" == res.group("action") and osname!="nt":
				insert = str(os.getuid())

			if "os_name" == res.group("action"):
				insert = platform.system()
			if "os_version" == res.group("action"):
				insert = platform.version()
			if "os_archi" == res.group("action"):
				insert = platform.architecture()[0]


			if res.group("action").startswith('mem_'):
				virtual = psutil.virtual_memory()
				if "mem_total" == res.group("action"):
					insert = sizeconvert(virtual.total)
				if "mem_available" == res.group("action"):
					insert = sizeconvert(virtual.available)
				if "mem_used" == res.group("action"):
					insert = sizeconvert(virtual.used)
				if "mem_free" == res.group("action"):
					insert = sizeconvert(virtual.free)
				if "mem_percent" == res.group("action"):
					insert = str(virtual.percent)

			if res.group("action").startswith('swap_'):
				swap =  psutil.swap_memory()
				if "swap_total" == res.group("action"):
					insert = sizeconvert(swap.total)
				if "swap_used" == res.group("action"):
					insert = sizeconvert(swap.used)
				if "swap_free" == res.group("action"):
					insert = sizeconvert(swap.free)
				if "swap_percent" == res.group("action"):
					insert = str(swap.percent)

			if "cpu_count" == res.group("action"):
				insert = str(psutil.cpu_count(logical=False))
			if "cpu_logical_count" == res.group("action"):
				insert = str(psutil.cpu_count(logical=True))
			if "cpu_percent" == res.group("action"):
				insert = str(psutil.cpu_percent(interval=0.1))

			if res.group("action").startswith('current_disk'):
				stack = inspect.stack()
				disk_info = get_disk_info(abspath(stack[1].filename))
				if "current_disk_device" == res.group("action"):
					insert = disk_info.get('device', '')
				if "current_disk_mountpoint" == res.group("action"):
					insert = disk_info.get('mountpoint', '')
				if "current_disk_fstype" == res.group("action"):
					insert = disk_info.get('fstype', '')
				if "current_disk_total" == res.group("action"):
					insert = str(disk_info.get('total_size', ''))
				if "current_disk_used" == res.group("action"):
					insert = str(disk_info.get('used_size', ''))
				if "current_disk_free" == res.group("action"):
					insert = str(disk_info.get('free_size', ''))
				if "current_disk_percent" == res.group("action"):
					insert = str(str(disk_info.get('percent', '')))

			if re.findall(reg_foreground, res.group("action")):
				for rest in re.finditer(reg_foreground,res.group("action")):
					if rest.group("color").isdigit():
						result = result.replace(f"%({rest.group()})%", fg(int(rest.group("color"))))
					else:
						result = result.replace(f"%({rest.group()})%", fg(rest.group("color")))

			if re.findall(reg_background,res.group("action")):
				for rest in re.finditer(reg_background,res.group("action")):
					if rest.group("color").isdigit():
						result = result.replace(f"%({rest.group()})%", bg(int(rest.group("color"))))
					else:
						result = result.replace(f"%({rest.group()})%", bg(rest.group("color")))

			if re.findall(reg_attribute,res.group("action")):
				for rest in re.finditer(reg_attribute,res.group("action")):
					if rest.group("color").isdigit():
						result = result.replace(f"%({rest.group()})%", attr(int(rest.group("color"))))
					else:
						result = result.replace(f"%({rest.group()})%", attr(rest.group("color")))

			if insert!=None:
				if res.group("padding")!=None and res.group("padding").isdigit():
					insert = insert.ljust(int(res.group("padding")), " ")
				result = result.replace(res.group(), str(insert))

		return result


#########################


##### SET HANDLER #####

class Handler:
	#Modifie le level du handler
	def setLevel(self, level, ops="=="):
		if ops==">=" or ops=="!=" or ops=="<" or ops==">" or ops=="<=" or ops=="==":
			self.operator = ops
		else:
			self.operator = "=="

		if isinstance(level, int) or level.isdigit():
			self.level = int(level)

	#Ajoute le formatter au handler
	def setFormatter(self, formatter):
		if hasattr(formatter, "pattern") and hasattr(formatter, "get"):
			self.formatter = formatter

	#Utilise le formatter pour formatter le texte avant de l'envoyer au write
	def format(self, message, level):
		if hasattr(self, "formatter"):
			message = self.formatter.get(message, level)

		return message

	def addFilter(self, filter):
		self.filter.append(filter)

	def removeFilter(self, filter):
		if filter in self.filter:
			self.filter.remove(filter)

	@impmagic.loader(
        {'module': 're'}
    )
	def check_filter(self):
		for fil in self.filter:
			if callable(fil):
				result = fil(self.message)
				if result!=True:
					return False
			else:
				try:
					compiled = re.compile(fil)
					if not compiled.findall(self.message):
						return False
				except re.error:
					print("Non valid regex pattern")
					return False
				except:
					return False
		return True


class Console_handler(Handler):
	def __init__(self, output=impmagic.get('sys').stdout, level=NOTSET, ops="=="):
		Handler.__init__(self)
		self.__output = output
		self.setLevel(level, ops)
		self.filter = []

	def write(self, message, level):
		self.message = self.format(message, level)
		if self.check_filter():
			if self.operator:
				if compare_level(self.level, self.operator, level):
					self.__output.write(self.message+"\n")
			else:
				self.__output.write(self.message+"\n")


class File_handler(Handler):
	def __init__(self, filename, rewrite=False, level=NOTSET, ops="=="):
		self.setLevel(level, ops)

		self.filename = filename
		self.rewrite = rewrite
		self.filter = []

	@impmagic.loader(
        {'module': 'os.path','submodule': ['exists', 'isfile']}
    )
	def set_output(self):
		#Utilise Formatter pour permettre de créer des noms de fichiers dynamique avec la syntaxe des formatter
		filename = self.get_filename()
		
		try:
			if exists(filename) and isfile(filename) and not self.rewrite:
				self.__output = open(filename, "a")
			else:
				self.__output = open(filename, "w")
		except Exception as e:
			print(e)
			return
	@impmagic.loader(
        {'module': 'os.path','submodule': ['abspath']}
    )
	def get_filename(self):
		return abspath(Formatter(self.filename).get("", self.level))

	def write(self, message, level):
		self.message = self.format(message, level)

		if self.check_filter():
			if self.operator:
				if compare_level(self.level, self.operator, level):
					self.set_output()
					self.__output.write(self.message+"\n")
					self.__output.close()
			else:
				self.set_output()
				self.__output.write(self.message+"\n")
				self.__output.close()


		del self.message



class RotateFile_handler(File_handler):
	def __init__(self, filename, rewrite=False, level=NOTSET, ops="==", maxBytes=None, backupCount=None):
		super().__init__(filename, rewrite, level, ops)
		self.maxBytes = maxBytes
		self.backupCount = backupCount
		self.current_count = 0
		self.current_file = ""
		self.filter = []

	#Retourne le fichier et rotation de fichier si nécessaire
	@impmagic.loader(
        {'module': 'os','submodule': ['remove', 'rename']},
        {'module': 'os.path','submodule': ['abspath', 'exists', 'getsize']}
    )
	def get_filename(self):
		filename = abspath(Formatter(self.filename).get("", self.level))

		if self.maxBytes!=None:
			if exists(filename):
				valid = False
				if self.current_file!="":
					filetest = self.current_file
				else:
					filetest = filename
				while not valid:
					size = getsize(filetest)+len(self.message)
					if size>self.maxBytes:
						if self.current_count>=self.backupCount-1:
							for i in reversed(range(1, self.backupCount)):
								if i==1:
									new = filename
									old = filename+"."+str(i)
								else:
									new = filename+"."+str(i-1)
									old = filename+"."+str(i)
								
								if exists(new) and exists(old):
									remove(old)
									print(f"remove: {old}")

								if exists(new):
									rename(new, old)
									print(f"move: {new}")
								valid = True
						else:
							self.current_count+=1
							filetest = filename+"."+str(self.current_count)
							if not exists(filetest):
								print(f"move: {filename}")
								rename(filename, filetest)
								valid = True
					else:
						valid = True

		self.current_file = filename		
		return filename

class SMTP_handler(Handler):
	@impmagic.loader(
        {'module': 'smtplib'}
    )
	def __init__(self, smtphost, fromaddr, toaddrs, subject, credentials=None, secure=None, timeout=5.0, level=NOTSET, ops="=="):
		if isinstance(smtphost, (list, tuple)):
			self.smtphost, self.smtpport = smtphost
		else:
			self.smtphost, self.smtpport = smtphost, None

		if not self.smtpport:
			self.smtpport = smtplib.SMTP_PORT

		if isinstance(credentials, (list, tuple)):
			self.username, self.password = credentials
		else:
			self.username = None

		self.fromaddr = fromaddr
		if isinstance(toaddrs, str):
			toaddrs = [toaddrs]
		self.toaddrs = toaddrs

		self.subject = subject
		self.secure = secure
		self.timeout = timeout

		self.filter = []

		self.setLevel(level, ops)


	def write(self, message, level):
		self.message = self.format(message, level)

		if self.check_filter():
			if self.operator:
				if compare_level(self.level, self.operator, level):
					self.send_mail(self.message)
			else:
				self.send_mail(self.message)

	@impmagic.loader(
        {'module': 'smtplib'},
        {'module': 'email', 'submodule': ['utils']},
        {'module': 'email.message', 'submodule': ['EmailMessage']}
    )
	def send_mail(self, message):
		try:
			smtp = smtplib.SMTP(self.smtphost, self.smtpport, timeout=self.timeout)
			msg = EmailMessage()
			msg['From'] = self.fromaddr
			msg['To'] = ','.join(self.toaddrs)
			msg['Subject'] = Formatter(self.subject).get("", self.level)
			msg['Date'] = utils.localtime()

			msg.set_content(message)
			if self.username:
				if self.secure is not None:
					smtp.ehlo()
					#smtp.starttls(*self.secure)
					smtp.starttls()
					smtp.ehlo()
				smtp.login(self.username, self.password)
			smtp.send_message(msg)
			smtp.quit()
		except Exception as e:
			print("{} - {}".format(type(e).__name__, e))

#######################

##### STANDALONE  #####
def log(message):
	ptr = Logger()
	hand = Console_handler(level=NOTSET)
	hand.setFormatter(Formatter("(msg)"))
	ptr.add_handler(hand)
	ptr.log(message)
def good(message):
	ptr = Logger()
	hand = Console_handler(level=GOOD)
	hand.setFormatter(Formatter("(fore:10)(msg)(attr:0)"))
	ptr.add_handler(hand)
	ptr.good(message)
def debug(message):
	ptr = Logger()
	hand = Console_handler(level=DEBUG)
	hand.setFormatter(Formatter("(fore:116)(msg)(attr:0)"))
	ptr.add_handler(hand)
	ptr.debug(message)
def info(message):
	ptr = Logger()
	hand = Console_handler(level=INFO)
	hand.setFormatter(Formatter("(fore:6)(msg)(attr:0)"))
	ptr.add_handler(hand)
	ptr.info(message)
def warning(message):
	ptr = Logger()
	hand = Console_handler(level=WARNING)
	hand.setFormatter(Formatter("(fore:11)(msg)(attr:0)"))
	ptr.add_handler(hand)
	ptr.warning(message)
def error(message):
	ptr = Logger()
	hand = Console_handler(level=ERROR)
	hand.setFormatter(Formatter("(fore:1)(msg)(attr:0)"))
	ptr.add_handler(hand)
	ptr.error(message)
def critical(message):
	ptr = Logger()
	hand = Console_handler(level=CRITICAL)
	hand.setFormatter(Formatter("(fore:9)(msg)(attr:0)"))
	ptr.add_handler(hand)
	ptr.critical(message)
#######################
