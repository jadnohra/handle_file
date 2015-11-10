import os,sys

g_dbg = '-dbg' in sys.argv or False

try:
	import mako.template as mako_temp
except ImportError:
	mako_temp = None
	pass
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
def endlvl(lvl):
	if 'type' not in lvl or lvl['type'] == '':
		print ''.join(['#']*(lvl['lvl']+1)), lvl['lines'][0]
	for l in reversed(lvl['lines'][1:]):
		print l
def main():
	k_titles = ['list', 'notes', 'sections', 'copy']
	ifp = largv[1]
	ofp = os.path.splitext(ifp)[0]+'.tex'
	lvld = []; file_start = True;
	li = 0
	with open(ifp, "r") as ifile:
		for line in ifile.readlines():
			li = li + 1
			if file_start and (line.startswith('#') or line.strip() == ''):
				pass
			else:
				file_start = False
				lvli = 0
				while lvli < len(line) and line[lvli] == "\t":
					lvli = lvli+1
				lvld.append([lvli, line[lvli:].rstrip(), li])
	clvld = []
	plvl = -1
	for lvl in lvld:
		if lvl[0] == plvl:
			clvld[-1]['lines'].append( [lvl[1], lvl[2]] )
		else:
			ptitle = clvld[-1]['lines'][-1][0] if (len(clvld) and len(clvld[-1]['lines'])) else ''
			ctdi = -1
			if ptitle in k_titles:
				title = ptitle
				clvld[-1]['lines'].pop()
			else:
				title = ptitle if ptitle in k_titles else ''
				ctdi = len(clvld)-1
				while ctdi > 0 and clvld[ctdi]['lvl'] > lvl[0]:
					ctdi = ctdi-1
				if ctdi > 0 and clvld[ctdi]['lvl'] == lvl[0]:
					title = clvld[ctdi]['title']; clvld[ctdi]['ctd_to'] = len(clvld);
					#print '>>>', ctdi, title, clvld[ctdi]
				else:
					ctdi = -1
			clvld.append({'lvl':lvl[0], 'lines':[ [lvl[1], lvl[2]] ], 'title':title, 'ctd_from':ctdi, 'ctd_to':-1, 'has_open_line':False})
			plvl = lvl[0]
	plvl = -1; lvl_state = {'section':0};
	close_stack = []
	fout = sys.stdout
	if largv_has(['-o']):
		fout = open(largv_get(['-o'], ''), 'w+')
	def begin_line(lvl, line, lvl_state):
		global slvl
		if lvl['has_open_line']:
			end_line(lvl, '')
		if lvl['title'] == 'sections':
			print >>fout, ''.join(['#']*(lvl_state['section'])),
		elif lvl['title'] == 'notes':
			print >>fout, '\\begin{note}'
		elif lvl['title'] == 'list':
			print >>fout, '\\item'
		lvl['has_open_line'] = True
	def end_line(lvl, line):
		if lvl['title'] == 'notes':
			print >>fout, '\\end{note}'
		lvl['has_open_line'] = False
	def begin_lvl(lvl, lvl_state):
		if lvl['ctd_from'] != -1:
			return
		if lvl['title'] == 'sections':
			lvl_state['section'] = lvl_state['section']+1
		elif lvl['title'] == 'list':
			print >>fout, '\\begin{enumerate}'
	def end_lvl(lvl, lvl_state):
		if lvl['ctd_to'] != -1:
			return
		if lvl['has_open_line']:
			end_line(lvl, '')
		if lvl['title'] == 'sections':
			lvl_state['section'] = lvl_state['section']-1
		if lvl['title'] == 'list':
			print >>fout, '\\end{enumerate}'
	for lvl in clvld:
		if lvl['lvl'] < plvl:
			while len(close_stack) and close_stack[-1]['lvl'] > lvl['lvl']:
				end_lvl(close_stack.pop(), lvl_state)
		begin_lvl(lvl, lvl_state)
		for line in lvl['lines']:
			begin_line(lvl, line, lvl_state)
			if g_dbg:
				print ''.join(['-']*(lvl['lvl'])),
			print >>fout, line[0]
		close_stack.append(lvl); plvl = lvl['lvl'];
	for lvl in reversed(close_stack):
		end_lvl(lvl, lvl_state)

largv = sys.argv
main()
