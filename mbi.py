from typing import Tuple
import io

def encode_mbi(value: int) -> bytes:
	data = bytearray()
	while value >= 0x80:
		data.append((value & 0x7F) | 0x80)
		value >>= 7
	data.append(value)
	return data

def decode_mbi(data: bytes) -> Tuple[int, int] | None:
	value = 0
	for size, byte in enumerate(data):
		value |= (byte & 0x7F) << (size * 7)
		if not byte & 0x80:
			return (size + 1, value)
	return None