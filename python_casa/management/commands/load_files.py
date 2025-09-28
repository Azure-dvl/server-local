import json
from os import path, listdir, stat
import pprint

import requests
from django.core.management.base import BaseCommand

folders = [
	'/run/media/azure/03D70BF637A6F80D/Anime/',
	'/run/media/azure/03D70BF637A6F80D/Doramas/',
	'/run/media/azure/ALMACEN/Movies/Animados/',
	'/run/media/azure/ALMACEN/Movies/Movies/',
	'/run/media/azure/ALMACEN/Movies/Series/',
	'/run/media/azure/ALMACEN/Games/',
	'/run/media/azure/618AE8FD102A7379/Games 2/',
	'/run/media/azure/618AE8FD102A7379/Emuladores/',
	'/run/media/azure/618AE8FD102A7379/Novelas/',
	'/run/media/azure/618AE8FD102A7379/Pedidos/'
]

class FSMapper:

	def __init__(self):
		self.files = []
		self.depth = 0
		self._c_folders = []
		# Almacenar rutas únicas de archivos indexados
		self.indexed_paths = set()

	def _log(self, *m):
		print(("\t" * self.depth) + f"{self.depth}.", *m)

	def seek(self, dirs: list, files=None):
		files = files if files is not None else self.files
		for d in dirs:
			new_d = self.expand(d)
			if new_d:
				files.append(new_d)

	def expand(self, f_path: str):
		if not path.exists(f_path):
			return None

		f = {
			"type": "",
			"name": "",
			"size": 0,
			"path": f_path,
			"files": [],
			"_depth": self.depth,
			"last_modified": 0
		}

		is_file = path.isfile(f_path)
		is_dir = path.isdir(f_path)
		f['type'] = "file" if is_file else "folder" if is_dir else "other"

		# Obtener el nombre base del archivo/carpeta
		f['name'] = path.basename(f_path.rstrip('/'))
		
		if is_file:
			f['size'] = path.getsize(f_path)
			f['last_modified'] = path.getmtime(f_path)
			# Agregar a rutas indexadas
			self.indexed_paths.add(f_path)
			# Actualizar tamaños en carpetas padres
			for fold in self._c_folders:
				fold['size'] += f['size']
		
		if is_dir:
			f['name'] += '/'
			self.depth += 1
			try:
				dir_contents = [path.join(f_path, item) for item in listdir(f_path)]
				self._c_folders.append(f)
				self.seek(dir_contents, f['files'])
				self._c_folders.pop()
			except PermissionError:
				print(f"Permiso denegado para: {f_path}")
			self.depth -= 1
		
		return f

class Command(BaseCommand):
	def handle(self, *args, **options):
		# Obtener archivos existentes en la base de datos
		try:
			response = requests.get('http://192.168.1.10:80/api/files/list/')
			existing_files = response.json() if response.status_code == 200 else []
			existing_paths = {f['path'] for f in existing_files}
		except requests.exceptions.RequestException as e:
			print(f"Error al obtener archivos existentes: {e}")
			existing_paths = set()

		# Inicializar y ejecutar mapper
		mapper = FSMapper()
		mapper.seek(folders)
		r = mapper.files.copy()

		# Filtrar solo nuevos archivos (que no están en la base de datos)
		new_files = []
		for root in r:
			stack = [root]
			while stack:
				current = stack.pop()
				if current['type'] == 'file' and current['path'] not in existing_paths:
					new_files.append(current)
				stack.extend(current['files'])

		# Enviar solo nuevos archivos si existen
		if new_files:
			print(f"Encontrados {len(new_files)} nuevos archivos. Subiendo...")
			response = requests.post(
				'http://192.168.1.10:80/api/files/create/',
				json={
					'server': "192.168.1.10",
					"files": r  # Enviamos la estructura completa, no solo los nuevos
				}
			)
			print(f"Respuesta del servidor: {response.status_code}")
		else:
			print("No se encontraron nuevos archivos")

		# Guardar output completo localmente (opcional)
		with open('./out.json', 'w+') as file:
			file.write(json.dumps(r))
			pprint.pprint(r)

