from typing import List, Any, Tuple, Dict
from mbi import decode_mbi, encode_mbi

class Package:
	def __init__(self, class_name: bytes, args_bytes: bytes, kwargs_bytes: bytes):
		self.class_name = b'' + class_name
		self.args_bytes = b'' + args_bytes
		self.kwargs_bytes = b'' + kwargs_bytes
	@property
	def upperPackageArgsBytes(self):
		size, _ = decode_mbi(self.args_bytes)
		return self.args_bytes[size:]

	def __bytes__(self):
		return b'' + encode_mbi(len(self.class_name)) + self.class_name \
			+ encode_mbi(len(self.upperPackageArgsBytes)) + self.upperPackageArgsBytes \
			+ encode_mbi(len(self.kwargs_bytes)) + self.kwargs_bytes


def class_to_pkg(class_name: str, args: List[Any], kwargs: Dict[Any, Any]) -> Package:
	'''
	function to transform a class creation into bytes.
	usage exmple: pkg = class_to_pkg("Test", ["arg1", "arg2"], {"arg3": 22}).

	could also put a class_to_pkg in args and in list, dict or tuple being args,
	for having Test2 that's a parameter of Test.

	it creates a Package object with :
	- class_name ex: b'Test'
	- args_bytes ex: b'6\\x1b[\\x02(\\x03int, \\x0222), (\\x03int, \\x0223)]' for args [22, 23]
	- kwargs_bytes ex: b'\\x17{\\x01\\x04'test': (\\x03int, \\x0224)}' for kwargs {'test': 24}

	types handled automatically are :
	- int
	- float
	- bytes
	- str
	- list
	- tuple
	- bool
	- dict

	upperPackageArgsBytes is used to remove first amount bytes that need to be removed in upper package's arg_bytes.

	encode_mbi and decode_mbi are used to deal with data amount and sizes.
	'''
	def getValue(arg) -> bytes:
		def getPackageRes(arg):
			result = b''
			result += encode_mbi(len(arg.class_name))
			result += arg.class_name
			result += b', '
			result += arg.args_bytes
			result += b', '
			result += arg.kwargs_bytes
			return result
		def getEasyTypeRes(arg):
			result = b''
			result += encode_mbi(len(arg.__class__.__name__))
			result += arg.__class__.__name__.encode()
			result += b', '
			if (arg.__class__.__name__ == 'bytes'):
				result += encode_mbi(len(arg))
				result += arg
			else:
				result += encode_mbi(len(str(arg)))
				result += str(arg).encode()
			return result
		container = ['list', 'dict', 'tuple']
		bracket_list = [b'[]', b'{}', b'()']
		if arg.__class__.__name__ == 'Package':
			val = getPackageRes(arg)
		elif arg.__class__.__name__ in container:
			val = encode_mbi(len(arg.__class__.__name__))
			val += arg.__class__.__name__.encode()
			val += b', '
			value = b''
			elem_amount = 0
			if arg.__class__.__name__ in ['list', 'tuple']:
				for elem in arg:
					elem_amount += 1
					value += getValue(elem)
			elif arg.__class__.__name__ in ['dict']:
				for key, elem in arg.items():
					elem_amount += 1
					value += encode_mbi(len(key))
					value += f"'{key}': ".encode()
					value += getValue(elem)
			if elem_amount > 0:
				value = value[:-2]
			value = b'' + chr(bracket_list[container.index(arg.__class__.__name__)][0]).encode() + encode_mbi(elem_amount) + value
			value += chr(bracket_list[container.index(arg.__class__.__name__)][-1]).encode()
			val += encode_mbi(len(value)) + value
		else:
			val = getEasyTypeRes(arg)
		return b'(' + val + b'), '
	def getArgs(*args) -> bytes:
		total_args = b''
		amount_args = 0
		for arg in args:
			total_args += getValue(arg)
			amount_args += 1
		if amount_args > 0:
			total_args = total_args[:-2]
		total_args = encode_mbi(amount_args) + total_args
		total_args = b'[' + total_args + b']'
		total_args = encode_mbi(len(total_args)) + total_args
		return total_args
	def getKwargs(**kwargs):
		total_kwargs = b''
		amount_kwargs = 0
		for key, value in kwargs.items():
			total_kwargs += encode_mbi(len(key))
			total_kwargs += f"'{key}': ".encode()
			total_kwargs += getValue(value)
			amount_kwargs += 1

		if amount_kwargs > 0:
			total_kwargs = total_kwargs[:-2]
		total_kwargs = encode_mbi(amount_kwargs) + total_kwargs
		total_kwargs = b'{' + total_kwargs + b'}'
		total_kwargs = encode_mbi(len(total_kwargs)) + total_kwargs
		return total_kwargs

	class_args = getArgs(*args)
	class_kwargs = getKwargs(**kwargs)
	class_name = class_name.encode()
	class_args = encode_mbi(len(class_args) + len(class_kwargs) + 2) + class_args
	res = Package(class_name, class_args, class_kwargs)
	return res

def pkg_to_class(class_name: bytes,
				handled_classes: List[object],
				handled_classes_name: List[bytes],
				args_bytes: bytes = b'',
				kwargs_bytes: bytes = b''):
	'''
	function to transform bytes into a class creation according to a strict format.

	args :
	- class_name: name of the class of the instance to create
	- handled_classes: all the class that will be handled in creation
	- handled_classes_name: all the names in bytes of the classes that will be handled in creation

	all handled_classes and handled_classes_name must be in the same order.

	handled_classes and handled_classes_name coudl also be function calls
	- args_bytes ex: b'\\x1b[\\x02(\\x03int, \\x0222), (\\x03int, \\x0223)]' for args [22, 23]
	- kwargs_bytes ex: b'\\x17{\\x01\\x04'test': (\\x03int, \\x0224)}' for kwargs {'test': 24}

	this create an instance of the class given the different params.

	if one of the classes/subclasses used is not in handled_classes and handled_classes_name it's going to be replaced by "".
	types handled automatically are :
	- int
	- float
	- bool
	- str
	- bytes
	- list
	- tuple
	- dict
	'''
	def getClass(class_name: bytes,
					handled_classes: List[object],
					handled_classes_name: List[bytes]) -> Tuple[object, bool]:
		if class_name in handled_classes_name:
			return handled_classes[handled_classes_name.index(class_name)]
		return None
	def _getArgValue(type: bytes, value: bytes, handled_classes: List[object], handled_classes_name: List[bytes]):
		def getAllClsArgsBytes(value: bytes) -> Tuple[bytes, bytes]:
			'''
			value: [args], {kwargs}
			'''
			j = 0
			size, args_size = decode_mbi(value[j:])
			val_args = value[j:j+args_size+size]
			j += size
			j += args_size + 2
			size, kwargs_size = decode_mbi(value[j:])
			val_kwargs = value[j:j+kwargs_size+size]
			j += size
			return val_args, val_kwargs # returns [args] and {kwargs}
		arg = b''
		if type == b'bytes':
			arg = value
		elif type == b'str': # TODO change to skip quotes
			arg = value.decode()
		elif type == b'bool':
			if value == b'False':
				arg = False
			else:
				arg = True
		elif type in [b'int', b'float']:
			arg = eval(type)(value)
		elif type in [b'dict', b'list', b'tuple']:
			size, container_size = decode_mbi(value)
			if type in [b'list', b'tuple']:
				arg = getArgs(value)
			elif type in [b'dict']:
				arg = getKwargs(value)
		elif type in handled_classes_name:
			cls_args, cls_kwargs = getAllClsArgsBytes(value)
			arg = pkg_to_class(type, handled_classes, handled_classes_name, cls_args, cls_kwargs)
		return arg
	def _getTypeAndValue(content: bytes) -> Tuple[int, bytes, bytes]:
				'''
				content:(type_size_mbi-type, value_size_mbi-value), ...
				'''
				i = 1
				size, type_size = decode_mbi(content[i:])
				i += size
				type = content[i:i+type_size]
				i += type_size + 2
				size, value_size = decode_mbi(content[i:])
				i += size
				val = content[i:i+value_size]
				i += value_size + 3
				return i, type, val
	def getArgs(args_bytes: bytes):
		'''
		args_bytes form: args_amount_mbi-(type_size_mbi-type, value_size_mbi value), (type_size_mbi-type2, value_size_mbi-value2)
		value can be either value
		or [args_size_mbi-args], {kwargs_size_mbi-kwargs}
		'''
		args = []
		i = 1
		size, args_amount = decode_mbi(args_bytes[i:])
		i += size
		while args_amount > 0:
			size, type, value = _getTypeAndValue(args_bytes[i:])
			i += size
			args.append(_getArgValue(type, value, handled_classes, handled_classes_name))
			args_amount -= 1
		return args
	def getKwargs(kwargs_bytes: bytes):
		def getKey(kwargs_bytes: bytes) -> Tuple[int, bytes]:
			'''
			kwargs_bytes[i:] :key_size_mbi-'key': value_size_mbi value, ...
			'''
			i = 0
			size, key_size = decode_mbi(kwargs_bytes[i:])
			i += size + 1
			type = kwargs_bytes[i:i+key_size]
			i += key_size + 3
			return i, type.decode()
		'''
		kwargs_bytes form: kwargs_amount_mbi key_size_mbi-'key': value_size_mbi value
		'''
		kwargs = {}
		i = 1
		size, kwargs_amount = decode_mbi(kwargs_bytes[i:])
		i += size
		while kwargs_amount > 0:
			size, key = getKey(kwargs_bytes[i:])
			i += size
			size, type, value = _getTypeAndValue(kwargs_bytes[i:])
			i += size
			kwargs[key] = _getArgValue(type, value, handled_classes, handled_classes_name)
			kwargs_amount -= 1
		return kwargs
	cls = getClass(class_name, handled_classes, handled_classes_name)
	if cls is None:
		return str()
	size, _ = decode_mbi(args_bytes[0:])
	args = getArgs(args_bytes[size:])
	if class_name == b'list':
		return cls(args)
	size, _ = decode_mbi(kwargs_bytes[0:])
	kwargs = getKwargs(kwargs_bytes[size:])
	return cls(*args, **kwargs)

def class_to_bytes(class_name: str, args: List[Any], kwargs: Dict[Any, Any]) -> bytes:
	return bytes(class_to_pkg(class_name, args, kwargs))

def bytes_to_class(data: bytes, handled_classes: List[object], handled_classes_name: List[bytes]) -> bytes:
	i = 0

	size, class_name_size = decode_mbi(data[i:])
	i += size
	class_name = data[i:i+class_name_size]
	i += class_name_size

	size, args_size = decode_mbi(data[i:])
	i += size
	args = data[i:i+args_size]
	i += args_size

	size, kwargs_size = decode_mbi(data[i:])
	i += size
	kwargs = data[i:i+kwargs_size]
	i += kwargs_size

	return pkg_to_class(class_name, handled_classes, handled_classes_name, args, kwargs)

class Test():
	def __init__(self, arg1, arg2=22) -> None:
		self.arg1 = arg1
		self.arg2 = arg2
	def __str__(self):
		return str(self.arg1) + ', ' + str(self.arg2)

	def __repr__(self):
		return str(self)

data = class_to_bytes('Test', ["arg1"], {"arg2": 24})
res = bytes_to_class(data, handled_classes=[Test], handled_classes_name=[b'Test'])
print(res)

pkg = class_to_pkg('Test', ["arg1"], {"arg2": 24})
res = pkg_to_class(pkg.class_name, [Test], [b'Test'], pkg.upperPackageArgsBytes, pkg.kwargs_bytes)
print(res)
