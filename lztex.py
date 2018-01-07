import os,sys
import copy, json
import re

g_dbg = '-dbg' in sys.argv or False
g_force_keep_indent = '-force_keep_indent' in sys.argv
g_kill_indent = True
g_enable_lzmath = False if '-no_lzmath' in sys.argv else True

g_re1 = re.compile(r"(\\)([A-Z])\b")
g_re1_subst = '\mathbb{\\2}'
g_re2 = re.compile(r"(])([A-Z])\b")
g_re2_subst = '\mathcal{\\2}'

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
def tex_escape(text):
	"""
		:param text: a plain text message
		:return: the message escaped to appear correctly in LaTeX
	"""
	conv = {
		'&': r'\&',
		'%': r'\%',
		'$': r'\$',
		'#': r'\#',
		'_': r'\_',
		'{': r'\{',
		'}': r'\}',
		'~': r'\textasciitilde{}',
		'^': r'\^{}',
		'\\': r'\textbackslash{}',
		'<': r'\textless',
		'>': r'\textgreater',
	}
	regex = re.compile('|'.join(re.escape(unicode(key)) for key in sorted(conv.keys(), key = lambda item: - len(item))))
	out = regex.sub(lambda match: conv[match.group()], text)
	return out
def main():
	global g_kill_indent
	k_meta_titles = ['ignore', 'bib']
	k_titles = ['keep', 'list', ':list', 'llist', ':llist', 'bullets', ':bullets', 'bbullets', ':bbullets', 'cases', ':cases', "eqn", "eqns" ,"eqns*", 'mm', 'm', 'notes', 'sections',
						'copy', 'tex', 'table', 'mtable', 'par', 'underline', 'footnote', 'foot', 'say', 'quote', 'footurl', 'onecol', 'tex_esc', 'href', 'url', ':colors', 'cite_all']
	k_titles2 = ['table', 'mtable', 'bullets', 'list', 'color', 'mark']
	def get_title(ptitle, out):
		if ptitle in k_titles:
			out[0] = ptitle; out[1] = ''; return True;
		elif ptitle.split(' ')[0] in k_titles2:
				ptitle_splt = ptitle.split()
				out[0] = ptitle_splt[0]; out[1] = ' '.join(ptitle_splt[1:]); out[2] = {};
				if '%%' in out[1]:
					params = '%%'.join(out[1].split('%%')[1:])
					out[2] = json.loads(params)
				return True
		out[0] = ''; out[1] = ''; out[2] = {};
		return False
	bib_out_lines = []
	ifp = largv[1]
	lvl_lines = []; file_start = True;
	li = 0
	with open(ifp, "r") as ifile:
		ignore_depth = -1; ignore_is_bib = False;
		for line in ifile.readlines():
			li = li + 1
			if file_start and (line.startswith('#') or line.strip() == ''):
				pass
			else:
				if '\t \t' in line:
					set_vt_col('yellow'); print 'Warning: space between tabs at line {}: "{}..."'.format(li, line.strip()[:5])
				file_start = False
				lvli = 0
				while lvli < len(line) and line[lvli] == "\t":
					lvli = lvli+1
				lvl_content = line[lvli:].rstrip()
				if ignore_depth == -1 or lvli <= ignore_depth:
					if lvl_content not in k_meta_titles:
						ignore_depth = -1
						lvl_lines.append([lvli, lvl_content, li])
					else:
						ignore_depth = lvli; ignore_is_bib = (lvl_content == 'bib');
				else:
						if ignore_is_bib:
							bib_out_lines.append(lvl_content)
	bib_cite_ids = []
	if len(bib_out_lines):
			bib_ofp = '{}{}'.format(os.path.splitext(ifp)[0], '.bib')
			bib_fout = open(bib_ofp, 'w+')
			bib_fout.write('% Auto-generated by lztex from [{}]\n\n'.format(os.path.split(ifp)[1]))
			bib_fout.write('\n'.join(bib_out_lines))
			regex = r"(\s|^)@.+{(.+),"
			for bib_line in bib_out_lines:
				matches = re.finditer(regex, bib_line)
				for match in matches:
					bib_cite_ids.append(match.groups()[1])
	#print lvl_lines
	def print_node_tree(node):
		def rep_parent(node):
			node['parent'] = node['parent']['line'] if node['parent'] else -1
			for n in node['children']:
				rep_parent(n)
		nnode = copy.deepcopy(node)
		rep_parent(nnode)
		print json.dumps(nnode, indent=1)
	def add_lines_recurse(rel_node, lvl_lines, i):
		def print_err():
			set_vt_col('red'); print 'Error: indent at line {}: "{}..."'.format(line[2], line[1][:5])
		line = lvl_lines[i]
		lvl_diff = line[0]-rel_node['lvl']
		title_mark = ''
		rec_parent = None
		if lvl_diff > 0 and rel_node['title'] == 'copy':
			parent = rel_node
			title_info = ['', '', '']
			nrel_node = parent
		else:
			while lvl_diff < 0:
				rel_node = rel_node['parent']; lvl_diff = lvl_diff+1;
				if rel_node == None:
					print_err(); return False;
			parent = rel_node['parent'] if lvl_diff == 0 else (rel_node if lvl_diff == 1 else None)
			if parent != None and parent['title'] in ['keep','mark']:
				parent = parent['parent']
				title_mark = parent['title_opts']
			title_info = ['', '', '']
			get_title(line[1], title_info)
			nrel_node = None
		if parent == None:
			print_err(); return False;
		node_title = title_info[0]
		if node_title == '':
			if parent['title'] in ['llist', 'bbullets']:
				rec_parent = parent
			if parent['rec_parent'] is not None:
				rec_parent = parent['rec_parent']
		line_node = {'parent':parent, 'rec_parent':rec_parent, 'line': line[2], 'lvl':line[0], 'content':line[1], 'children':[], 'title':node_title, 'title_opts':title_info[1], 'title_params':title_info[2], 'title_mark':title_mark, 'lvl_state':{}}
		if parent['title'] in ['table', 'mtable']:
			is_sep = line_node['content'] in ['-', '--']
			is_ext_sep =  any([line_node['content'].startswith(x) for x in ['- ', '-- ']])
			if is_sep or is_ext_sep:
				line_node['table_row_sep'] = True
				if is_ext_sep:
					line_node['title_opts'] = ' '.join(line_node['content'].split(' ')[1:])
				if len(parent['children']):
					parent['children'][-1]['table_last_row'] = True
		if line_node['title'] not in ['keep', 'mark']:
			parent['children'].append(line_node)
		if i+1 < len(lvl_lines):
			if add_lines_recurse(nrel_node if nrel_node else line_node, lvl_lines, i+1) == False:
				return False
		if line_node['title'] in ['table', 'mtable']:
			if len(line_node['children']):
				line_node['children'][-1]['table_last_row'] = True
		if parent['title'] == 'cases':
			parent['children'][-1]['case_last_row'] = True
		return True
	root_node = {'parent':None, 'rec_parent':None, 'line':-1, 'lvl':-1, 'children':[], 'title':'_root', 'title_opts':'', 'title_params':{}, 'lvl_state':{}}
	add_lines_recurse(root_node, lvl_lines, 0)
	#print_node_tree(root_node)
	fout = sys.stdout
	if largv_has(['-o']):
		ofp = largv_get(['-o'], '')
		if g_force_keep_indent == False and (os.path.splitext(ofp)[1] == '.md'): # Markdown will treat tabbed text as verbatim, we don't want this.
			g_kill_indent = True
		fout = open(ofp, 'w+')
	def do_lzmath(strng):
		def do_rep(strng):
			sub = strng
			sub = re.sub(g_re1, g_re1_subst, sub)
			sub = re.sub(g_re2, g_re2_subst, sub)
			return sub
		def do_split_2(strng, markers, reps):
			splt = strng.split(markers[0])
			strng1 = ''
			is_open = False
			for i in range(len(splt)):
				is_open = (i%2 == 1)
				if is_open:
					end_splt = splt[i].split(markers[1])
					strng1 = strng1 + reps[0] + do_rep(end_splt[0]) + reps[1] + (end_splt[1] if len(end_splt) > 1 else '')
				else:
					strng1 = strng1 + splt[i]
			return strng1
		def do_split_1(strng, marker, reps):
			splt = strng.split(marker)
			strng1 = ''
			is_open = False
			for i in range(len(splt)):
				is_open = (i%2 == 1)
				if is_open:
					xfm = do_split_2( do_split_2(splt[i], ('{', '}'), ('\\{','\\}')), ('  ', '  '), ('{','}'))
					strng1 = strng1 + reps[0] + do_rep(xfm) + reps[1]
				else:
					strng1 = strng1 + splt[i]
			return strng1
		if g_enable_lzmath:
				strng1 = do_split_1(strng, '\t\t', (' $$', '$$ '))
				strng2 = do_split_1(strng1, '\t', (' $', '$ '))
				return strng2
		else:
			return strng
	def indented_str(node, lvl_state, strng):
		is_copy_node = (lvl_state['title_node'] is not None) and (lvl_state['title_node']['title'] == 'copy')
		if is_copy_node == False:
			if (g_kill_indent):
				return strng
			else:
				return ''.join(['\t']*node['lvl']) + strng
		else:
			return ''.join(['\t']*(node['lvl']-1)) + strng
	def begin_line(lvl, node, lvl_state):
		line = node['content']
		if lvl['title'] == 'sections':
			print >>fout, '\n', ''.join(['#']*(lvl_state.get('section', 0))),
		elif lvl['title'] == 'notes':
			print >>fout, indented_str(node, lvl_state, '\\begin{note}')
		elif lvl['title'] == 'href':
			print >>fout, indented_str(node, lvl_state, '{'),
		elif (lvl['title'] in ['list', 'bullets', 'llist', 'bbullets']) or (lvl['rec_parent'] is not None and lvl['rec_parent']['title'] in ['llist', 'bbullets']):
			print >>fout, indented_str(node, lvl_state, '\\item')
		#elif lvl['title'] == 'mtable':
		#	print >>fout, indented_str(node, lvl_state, '$'),
	def end_line(lvl, node, lvl_state):
		line = node['content']
		if lvl['title'] == 'notes':
			print >>fout, indented_str(node, lvl_state, '\\end{note}')
		elif lvl['title'] in ['table', 'mtable']:
			if node.get('table_row_sep', False):
				lvl_state['row_cnt'] = lvl_state['row_cnt'] + 1
				lvl_state['col_cnt'] = 0
				sep_tex = ''
				if line.startswith('--'):
					sep_tex = lvl['title_params'].get('--', '\\\\ \hline')
				else:
					sep_tex = lvl['title_params'].get('-', '\\\\')
				print >>fout, indented_str(node, lvl_state, '{} {}'.format(sep_tex, node['title_opts']))
			else:
				if node.get('table_last_row', False) == False:
					print >>fout, indented_str(node, lvl_state, '& '),
				lvl_state['col_cnt'] = lvl_state['col_cnt'] + 1
			#if lvl['title'] == 'mtable':
			#	print >>fout, indented_str(node, lvl_state, '$')
		elif lvl['title'] == 'cases':
			if node.get('cases_last_row', False):
					print >>fout, indented_str(node, lvl_state, '\\\\ '),
		elif lvl['title'] == 'href':
			print >>fout, indented_str(node, lvl_state, '}'),
	def do_line(lvl, node, lvl_state, glob_state):
		def print_content(node, lvl_state, strng, line_ret = True, enable_lzmath = False):
			if strng != 'blank':
				print >>fout, indented_str(node, lvl_state, do_lzmath(strng) if enable_lzmath else strng),
				if line_ret:
					print >>fout, ''
		if lvl['title'].startswith(':'):
			tag = lvl['title'][1:]
			if 'tag' == 'colors':
				if tag in glob_state['settings']:
					glob_state['settings'][tag].append(node['content'])
				else:
					glob_state['settings'][tag] = [node['content']]
			else:
				glob_state['settings'][tag] = node['content']
		else:
			if lvl['title'] in ['table', 'mtable']:
				if node.get('table_row_sep', False):
					return
			elif lvl['title'] in ['tex_esc', 'footurl', 'say', 'url']:
				print_content(node, lvl_state, tex_escape(node['content']))
				return
			elif lvl['title'] in ['quote']:
				print_content(node, lvl_state, node['content'].replace('- ', ''))
				return
			print_content(node, lvl_state, node['content'], lvl['title'] not in ['href'], True)
	def begin_lvl(lvl, lvl_state, title_node, glob_state):
		def get_title_opt(lvl):
			opt = lvl.get('title_opts', '')
			return opt if len(opt) else glob_state['settings'].get(lvl['title'],'')
		lvl_state['title_node'] = title_node # TODO, do this during pre-processing, add it to lvl instead of lvl_state
		if lvl['title'] == 'sections':
			glob_state['section'] = glob_state.get('section', 0)+1
			lvl_state['section'] = glob_state['section']
		elif lvl['title'] in ['list', 'llist']:
			print >>fout, indented_str(lvl, lvl_state, '{} {}'.format('\\begin{enumerate}', get_title_opt(lvl) ))
		elif lvl['title'] in ['bullets', 'bbullets']:
			print >>fout, indented_str(lvl, lvl_state, '{} {}'.format('\\begin{itemize}', get_title_opt(lvl) ))
		elif lvl['title'] == 'cases':
			print >>fout, indented_str(lvl, lvl_state, '{} {}'.format('\\begin{cases}', get_title_opt(lvl) ))
		elif lvl['title'] == 'onecol':
			print >>fout, indented_str(lvl, lvl_state, '{} {}'.format('\\begin{strip}', lvl.get('title_opts', '')))
		elif lvl['title'] == 'eqns*':
			print >>fout, indented_str(lvl, lvl_state, '\\begin{align*}')
		elif lvl['title'] == 'eqns':
			print >>fout, indented_str(lvl, lvl_state, '\\begin{align}')
		elif lvl['title'] == 'eqn':
			print >>fout, indented_str(lvl, lvl_state, '\\begin{equation}')
		elif lvl['title'] == 'mm':
			print >>fout, indented_str(lvl, lvl_state, '$$')
		elif lvl['title'] == 'm':
			print >>fout, indented_str(lvl, lvl_state, '$')
		elif lvl['title'] in ['table', 'mtable']:
			lvl_state['row_cnt'] = 0; lvl_state['col_cnt'] = 0;
			if any([x in lvl['title_params'] for x in ['col', 'row']]):
				lvl_state['has_group'] = True
				print >>fout, indented_str(lvl, lvl_state, '\\begingroup')
				if 'row' in lvl['title_params']:
					row_cmd = '\\renewcommand{{\\arraystretch}}{{ {} }}'.format(lvl['title_params']['row'])
					print >>fout, indented_str(lvl, lvl_state, row_cmd)
				if 'col' in lvl['title_params']:
					col_cmd = '\\setlength{{\\tabcolsep}}{{ {} }}'.format(lvl['title_params']['col'])
					print >>fout, indented_str(lvl, lvl_state, col_cmd)
			print >>fout, indented_str(lvl, lvl_state, '\\begin{tabular}'),
			print >>fout, lvl['title_opts']
		elif lvl['title'] == 'tex':
			print >>fout, indented_str(lvl, lvl_state, '\\begin{identity}')
		elif lvl['title'] == 'par':
			print >>fout, indented_str(lvl, lvl_state, '\\par')
		elif lvl['title'] in ['footnote', 'foot']:
			print >>fout, indented_str(lvl, lvl_state, '\\footnote{')
		elif lvl['title'] == 'footurl':
			print >>fout, indented_str(lvl, lvl_state, '\\footnote{\\url{')
		elif lvl['title'] in ['say']:
			print >>fout, indented_str(lvl, lvl_state, '\\say{')
		elif lvl['title'] in ['underline']:
			print >>fout, indented_str(lvl, lvl_state, '\\ul{')
		elif lvl['title'] in ['quote']:
			print >>fout, indented_str(lvl, lvl_state, '\\begin{quote}')
		elif lvl['title'] == 'href':
			print >>fout, indented_str(lvl, lvl_state, '\\href'),
		elif lvl['title'] == 'url':
			print >>fout, indented_str(lvl, lvl_state, '\\url{'),
		elif lvl['title'] == 'color':
			colors = lvl['title_opts'].split(' ')
			cmd_fore = ('\\color{{{}}}'  if '{' not in colors[0] else '\\color{}').format(colors[0])
			cmd_back = '\\colorbox{{{}}}'.format(colors[1] if '{' not in colors[1] else colors[1]) if (len(colors) >= 2) else ''
			cmd_par = '\\parbox{0.9\\textwidth}' if len(cmd_back) else ''
			print >>fout, indented_str(lvl, lvl_state, '\\begingroup {}{}{{{}'.format(cmd_fore, cmd_back, cmd_par))
		elif lvl['title'] == 'keep':
			1
		elif lvl['title'] == 'cite_all':
			if len(bib_cite_ids):
				cite_list = ', '.join(['@{}'.format(x) for x in bib_cite_ids])
				print >>fout, '--- \nnocite: |\n {}\n--- \n'.format(cite_list)
		elif lvl['title'] == '' and len(lvl['children']) > 0:
			if lvl['rec_parent'] is not None:
				if lvl['rec_parent']['title'] == 'llist':
					print >>fout, indented_str(lvl['rec_parent'], lvl_state, '{} {}'.format('\\begin{enumerate}', get_title_opt(lvl['rec_parent']) ))
				elif lvl['rec_parent']['title'] == 'bbullets':
					print >>fout, indented_str(lvl['rec_parent'], lvl_state, '{} {}'.format('\\begin{itemize}', get_title_opt(lvl['rec_parent']) ))
	def end_lvl(lvl, lvl_state, glob_state):
		if lvl['title'] == 'sections':
			glob_state['section'] = glob_state.get('section', 0)-1
		elif lvl['title'] in ['list', 'llist']:
			print >>fout, indented_str(lvl, lvl_state, '\\end{enumerate}')
		elif lvl['title'] in ['bullets', 'bbullets']:
			print >>fout, indented_str(lvl, lvl_state, '\\end{itemize}')
		elif lvl['title'] == 'cases':
			print >>fout, indented_str(lvl, lvl_state, '\\end{cases}')
		elif lvl['title'] == 'onecol':
			print >>fout, indented_str(lvl, lvl_state, '\\end{strip}')
		elif lvl['title'] == 'eqns*':
			print >>fout, indented_str(lvl, lvl_state, '\\end{align*}')
		elif lvl['title'] == 'eqns':
			print >>fout, indented_str(lvl, lvl_state, '\\end{align}')
		elif lvl['title'] == 'eqn':
				print >>fout, indented_str(lvl, lvl_state, '\\end{equation}')
		elif lvl['title'] == 'mm':
			print >>fout, indented_str(lvl, lvl_state, '$$')
		elif lvl['title'] == 'm':
			print >>fout, indented_str(lvl, lvl_state, '$')
		elif lvl['title'] in ['table', 'mtable']:
			print >>fout, indented_str(lvl, lvl_state, '\\end{tabular}')
			if lvl_state.get('has_group', False):
				print >>fout, indented_str(lvl, lvl_state, '\\endgroup')
		elif lvl['title'] == 'tex':
			print >>fout, indented_str(lvl, lvl_state, '\\end{identity}')
		elif lvl['title'] in ['footnote', 'foot']:
			print >>fout, indented_str(lvl, lvl_state, '}')
		elif lvl['title'] in ['say']:
			print >>fout, indented_str(lvl, lvl_state, '}')
		elif lvl['title'] in ['underline']:
			print >>fout, indented_str(lvl, lvl_state, '}')
		elif lvl['title'] in ['quote']:
			print >>fout, indented_str(lvl, lvl_state, '\\end{quote}')
		elif lvl['title'] == 'footurl':
			print >>fout, indented_str(lvl, lvl_state, '}}')
		elif lvl['title'] == 'url':
			print >>fout, indented_str(lvl, lvl_state, '}')
		elif lvl['title'] == 'color':
				print >>fout, indented_str(lvl, lvl_state, '} \\endgroup')
		elif lvl['title'] == 'keep':
			1
		elif lvl['title'] == '' and len(lvl['children']) > 0:
			if lvl['rec_parent'] is not None:
				if lvl['rec_parent']['title'] == 'llist':
					print >>fout, indented_str(lvl['rec_parent'], lvl_state, '\\end{enumerate}')
				elif lvl['rec_parent']['title'] == 'bbullets':
					print >>fout, indented_str(lvl['rec_parent'], lvl_state, '\\end{itemize}')
	def process_nodes_recurse(node, title_node, glob_state):
		lvl_state = node['lvl_state']
		begin_lvl(node, lvl_state, title_node, glob_state)
		for cn in node['children']:
			begin_line(node, cn, lvl_state)
			if cn['title'] == '':
				do_line(node, cn, lvl_state, glob_state)
			process_nodes_recurse(cn, title_node if cn['title'] == '' else cn, glob_state)
			end_line(node, cn, lvl_state)
		end_lvl(node, lvl_state, glob_state)
	glob_state = { 'settings':{} }
	process_nodes_recurse(root_node, None, glob_state)

largv = sys.argv
main()
