import os,sys,os.path,subprocess,hashlib

g_dbg = '-dbg' in sys.argv or False
g_verbose = '-verbose' in sys.argv or False
g_no_cache = '-no_cache' in sys.argv or False

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
def fphere():
	return os.path.dirname(os.path.realpath(__file__))
def main():
	def handle_file(fp, old_md5):
		new_md5 = hashlib.md5(open(fp, 'r').read()).hexdigest()
		if new_md5 != old_md5:
			handletool = os.path.join(fphere(), 'handle_file.sh')
			pop_in = [handletool, ofp]
			#print ''; sys.stdout.flush();
			pop = subprocess.Popen(pop_in)
			pop.wait()
			#print ''
		else:
			if g_verbose:
				print '  (cached)'
	ifp = largv[1]
	ofd = os.path.dirname(os.path.realpath(ifp))
	ofp = ''; ofile = None; do_handle = False; old_md5 = None;
	find = 0
	with open(ifp, "r") as ifile:
		for line in ifile.readlines():
			if (line.startswith('--[') or line.startswith('-=['))  and line.rstrip().endswith(']'):
				if ofile:
					ofile.close()
					if (do_handle):
						handle_file(ofp, old_md5)
				do_handle = line.startswith('-=[')
				ofn = line[len('--['):-2]; ofp = os.path.join(ofd, ofn);
				if do_handle and not g_no_cache:
					old_md5 = hashlib.md5(open(ofp, 'r').read()).hexdigest()
				ofile = open(ofp, "w")
				find = find+1
				if g_dbg or g_verbose:
					set_vt_col('yellow'); print ' {}'.format(ofn); set_vt_col('default'); sys.stdout.flush();
			else:
				if line.startswith('--#') == False:
					ofile.write(line)
	if ofile:
		ofile.close()
		if (do_handle):
			handle_file(ofp, old_md5)
largv = sys.argv
main()
