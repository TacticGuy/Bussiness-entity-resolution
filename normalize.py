"""Small, deterministic normalizers used by blocking and feature extraction."""
import re
import unicodedata

try:
	from unidecode import unidecode
except ImportError:
	def unidecode(value):
		return value


_POSTAL_RE = re.compile(r"\b(\d{4,6})\b")


def normalize_text(value):
	"""Return a case-folded ASCII-ish form suitable for exact blocking."""
	if value is None:
		return ""
	value = unidecode(str(value)).casefold()
	cleaned = [character if (character == "_" or
							 unicodedata.category(character)[0] in "LNM") else " "
			   for character in value]
	return re.sub(r"\s+", " ", "".join(cleaned)).strip()


def normalize_name(value):
	return normalize_text(value)


def normalize_address(value):
	return normalize_text(value)


def postal_codes(value):
	if not isinstance(value, str):
		return set()
	return set(_POSTAL_RE.findall(value))


def blocking_keys(name, address):
	"""Generate conservative, multi-field keys for candidate retrieval."""
	name_norm = normalize_name(name)
	address_norm = normalize_address(address)
	name_tokens = name_norm.split()
	address_tokens = address_norm.split()
	keys = set()
	if name_norm:
		keys.add("name:" + name_norm)
		keys.update("nt:" + token for token in name_tokens if len(token) >= 4)
	for code in postal_codes(address):
		keys.add("postal:" + code)
	for token in address_tokens:
		if len(token) >= 5:
			keys.add("at:" + token)
	return keys
