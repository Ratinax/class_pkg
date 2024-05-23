from classToPkg import *

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
