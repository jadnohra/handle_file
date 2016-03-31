import os,sys,os.path

g_dbg = '-dbg' in sys.argv or False
g_verbose = '-verbose' in sys.argv or False

k_vt_col_map = { '':'\x1b[0m', 'default':'\x1b[0m', 'black':'\x1b[30m', 'red':'\x1b[31m', 'green':'\x1b[32m', 'yellow':'\x1b[33m',
	'blue':'\x1b[34m', 'magenta':'\x1b[35m', 'cyan':'\x1b[36m', 'white':'\x1b[37m',
	'bdefault':'\x1b[49m', 'bblack':'\x1b[40m', 'bred':'\x1b[41m', 'bgreen':'\x1b[42m', 'byellow':'\x1b[43m',
	'bblue':'\x1b[44m', 'bmagenta':'\x1b[45m', 'bcyan':'\x1b[46m', 'bwhite':'\x1b[47m' }
vt_cm = k_vt_col_map
def set_vt_col(col):
	sys.stdout.write(k_vt_col_map[col])
def unistr(str):
	if not isinstance(str, unicode):
		return unicode(str, "utf-8")
	return str
largv = []
def largv_has(keys):
	for i in range(len(keys)):
		 if (keys[i] in largv):
			return True
	return False
def largv_has_key(keys):
	for key in keys:
		ki = largv.index(key) if key in largv else -1
		if (ki >= 0 and ki+1 < len(largv)):
			return True
	return False
def largv_get(keys, dflt):
	if ( hasattr(sys, 'argv')):
		for key in keys:
			ki = largv.index(key) if key in largv else -1
			if (ki >= 0 and ki+1 < len(largv)):
				return largv[ki+1]
	return dflt
def largv_geti(i, dflt):
	if (i >= len(largv)):
		return dflt
	return largv[i]
def main():
	ifp = largv[1]
	ofd = os.path.dirname(ifp)
	ofile = None
	with open(ifp, "r") as ifile:
		for line in ifile.readlines():
			if line.startswith('--[') and line.rstrip().endswith(']'):
				if ofile:
					ofile.close()
				ofp = line[len('--['):-2]
				ofile = open(os.path.join(ofd, ofp), "w")
				if g_dbg or g_verbose:
					set_vt_col('green'); print ' {}'.format(ofp); set_vt_col('default');
			else:
				if line.startswith('--#') == False:
					ofile.write(line)
	if ofile:
		ofile.close()
largv = sys.argv
main()
