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
def main():
	k_ignore = 'ignore'
	k_titles = ['list', 'bullets', 'notes', 'sections', 'copy', 'tex', 'table']
	k_titles2 = ['table']
	def get_title(ptitle, out):
		if ptitle in k_titles:
			out[0] = ptitle; out[1] = ''; return True;
		elif ptitle.split(' ')[0] in k_titles2:
				ptitle_splt = ptitle.split()
				out[0] = ptitle_splt[0]; out[1] = ' '.join(ptitle_splt[1:]);
				return True
		out[0] = ''; out[1] = '';
		return False
	ifp = largv[1]
	ofp = os.path.splitext(ifp)[0]+'.tex'
	lvld = []; file_start = True;
	li = 0
	with open(ifp, "r") as ifile:
		ignore_depth = -1
		for line in ifile.readlines():
			li = li + 1
			if file_start and (line.startswith('#') or line.strip() == ''):
				pass
			else:
				file_start = False
				lvli = 0
				while lvli < len(line) and line[lvli] == "\t":
					lvli = lvli+1
				lvl_content = line[lvli:].rstrip()
				if ignore_depth == -1 or lvli <= ignore_depth:
					if lvl_content != k_ignore:
						ignore_depth = -1
						lvld.append([lvli, lvl_content, li])
					else:
						ignore_depth = lvli
	clvld = []; plvl = -1;
	for lvl in lvld:
		if lvl[0] == plvl:
			clvld[-1]['lines'].append( [lvl[1], lvl[2]] )
		else:
			ptitle = clvld[-1]['lines'][-1][0] if (len(clvld) and len(clvld[-1]['lines'])) else ''
			ctdi = -1; title_info = ['', '']; title = '';
			if get_title(ptitle, title_info):
				title = title_info[0]
				clvld[-1]['lines'].pop()
			else:
				get_title(ptitle, title_info)
				title = title_info[0]
				ctdi = len(clvld)-1
				while ctdi > 0 and clvld[ctdi]['lvl'] > lvl[0]:
					ctdi = ctdi-1
				if ctdi > 0 and clvld[ctdi]['lvl'] == lvl[0]:
					title = clvld[ctdi]['title']; clvld[ctdi]['ctd_to'] = len(clvld);
					#print '>>>', ctdi, title, clvld[ctdi]
				else:
					ctdi = -1
			clvld.append({'lvl':lvl[0], 'lines':[ [lvl[1], lvl[2]] ], 'title':title, 'opts':title_info[1], 'ctd_from':ctdi, 'ctd_to':-1, 'has_open_line':False, 'counter':0})
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
			print >>fout, '\n', ''.join(['#']*(lvl_state['section'])),
		elif lvl['title'] == 'notes':
			print >>fout, '\\begin{note}'
		elif lvl['title'] == 'list' or lvl['title'] == 'bullets':
			print >>fout, '\\item',
		lvl['has_open_line'] = True
	def end_line(lvl, line):
		if lvl['title'] == 'notes':
			print >>fout, '\\end{note}'
		lvl['has_open_line'] = False
		lvl['counter'] = lvl['counter'] + 1
	def do_line(lvl, line, lvl_state):
		def print_content(str):
			if str != 'blank':
				print >>fout, line[0]
		if lvl['title'] == 'table':
			if line[0] == '-' or line[0] == '--':
				lvl['row_cnt'] = lvl['row_cnt'] + 1
				lvl['col_cnt'] = 0
				print >>fout, '\\\\'
				if line[0] == '--':
					print >>fout, '\hline'
			else:
				if lvl['col_cnt'] > 0:
					print >>fout, '& ',
				print_content(line[0])
				lvl['col_cnt'] = lvl['col_cnt'] + 1
		else:
			print_content(line[0])
	def begin_lvl(lvl, lvl_state):
		if lvl['ctd_from'] != -1:
			if clvld[lvl['ctd_from']]['has_open_line']:
				end_line(lvl, '')
				clvld[lvl['ctd_from']]['has_open_line'] = False
				# continue any specific properties
				noctd_keys = lvl.keys()
				for k,v in clvld[lvl['ctd_from']].items():
					if k not in noctd_keys:
						lvl[k] = v
			return
		if lvl['title'] == 'sections':
			lvl_state['section'] = lvl_state['section']+1
		elif lvl['title'] == 'list':
			print >>fout, '\\begin{enumerate}'
		elif lvl['title'] == 'bullets':
			print >>fout, '\\begin{itemize}'
		elif lvl['title'] == 'table':
			lvl['row_cnt'] = 0; lvl['col_cnt'] = 0;
			print >>fout, '\\begin{tabular}',
			print >>fout, lvl['opts'],
		elif lvl['title'] == 'tex':
			print >>fout, '\\begin{identity}'
	def end_lvl(lvl, lvl_state):
		if lvl['ctd_to'] != -1:
			return
		if lvl['has_open_line']:
			end_line(lvl, '')
		if lvl['title'] == 'sections':
			lvl_state['section'] = lvl_state['section']-1
		elif lvl['title'] == 'list':
			print >>fout, '\\end{enumerate}'
		elif lvl['title'] == 'bullets':
			print >>fout, '\\end{itemize}'
		elif lvl['title'] == 'table':
			print >>fout, '\\end{tabular}'
		elif lvl['title'] == 'tex':
			print >>fout, '\\end{identity}'
	#print '\n\n'.join(['  ,  '.join(['{}:{}'.format(y[0], y[1]) for y in x.items()]) for x in clvld])
	for lvl in clvld:
		if lvl['lvl'] < plvl:
			while len(close_stack) and close_stack[-1]['lvl'] > lvl['lvl']:
				end_lvl(close_stack.pop(), lvl_state)
		begin_lvl(lvl, lvl_state)
		for line in lvl['lines']:
			begin_line(lvl, line, lvl_state)
			if g_dbg:
				print ''.join(['-']*(lvl['lvl'])),
			do_line(lvl, line, lvl_state)
		close_stack.append(lvl); plvl = lvl['lvl'];
	for lvl in reversed(close_stack):
		end_lvl(lvl, lvl_state)

largv = sys.argv
main()
