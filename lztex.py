import os,sys
import copy, json

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
	k_titles = ['list', 'bullets', 'mm', 'm', 'notes', 'sections', 'copy', 'tex', 'table', 'par']
	k_titles2 = ['table']
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
	ifp = largv[1]
	ofp = os.path.splitext(ifp)[0]+'.tex'
	lvl_lines = []; file_start = True;
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
						lvl_lines.append([lvli, lvl_content, li])
					else:
						ignore_depth = lvli
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
			title_info = ['', '', '']
			get_title(line[1], title_info)
			nrel_node = None
		if parent == None:
			print_err(); return False;
		line_node = {'parent':parent, 'line': line[2], 'lvl':line[0], 'content':line[1], 'children':[], 'title':title_info[0], 'title_opts':title_info[1], 'title_params':title_info[2], 'lvl_state':{}}
		if parent['title'] == 'table':
			is_sep = line_node['content'] in ['-', '--']
			is_ext_sep =  any([line_node['content'].startswith(x) for x in ['- ', '-- ']])
			if is_sep or is_ext_sep:
				line_node['table_row_sep'] = True
				if is_ext_sep:
					line_node['title_opts'] = ' '.join(line_node['content'].split(' ')[1:])
				if len(parent['children']):
					parent['children'][-1]['table_last_col'] = True
		parent['children'].append(line_node)
		if i+1 < len(lvl_lines):
			if add_lines_recurse(nrel_node if nrel_node else line_node, lvl_lines, i+1) == False:
				return False
		if line_node['title'] == 'table':
			if len(line_node['children']):
				line_node['children'][-1]['table_last_col'] = True
		return True
	root_node = {'parent':None, 'line':-1, 'lvl':-1, 'children':[], 'title':'_root', 'title_opts':'', 'title_params':{}, 'lvl_state':{}}
	add_lines_recurse(root_node, lvl_lines, 0)
	#print_node_tree(root_node)
	fout = sys.stdout
	if largv_has(['-o']):
		fout = open(largv_get(['-o'], ''), 'w+')
	def indented_str(node, lvl_state, strng):
		if lvl_state['indent_content']:
			return ''.join(['\t']*node['lvl']) + strng
		else:
			return strng
	def begin_line(lvl, node, lvl_state):
		line = node['content']
		if lvl['title'] == 'sections':
			print >>fout, '\n', ''.join(['#']*(lvl_state.get('section', 0))),
		elif lvl['title'] == 'notes':
			print >>fout, indented_str(node, lvl_state, '\\begin{note}')
		elif lvl['title'] == 'list' or lvl['title'] == 'bullets':
			print >>fout, indented_str(node, lvl_state, '\\item'),
	def end_line(lvl, node, lvl_state):
		line = node['content']
		if lvl['title'] == 'notes':
			print >>fout, indented_str(node, lvl_state, '\\end{note}')
		if lvl['title'] == 'table':
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
				if node.get('table_last_col', False) == False:
					print >>fout, indented_str(node, lvl_state, '& '),
				lvl_state['col_cnt'] = lvl_state['col_cnt'] + 1
	def do_line(lvl, node, lvl_state):
		def print_content(node, lvl_state, strng):
			if strng != 'blank':
				print >>fout, indented_str(node, lvl_state, strng)
		if lvl['title'] == 'table':
			if node.get('table_row_sep', False):
				return
		print_content(node, lvl_state, node['content'])
	def begin_lvl(lvl, lvl_state, indent_content):
		lvl_state['indent_content'] = (indent_content and lvl['title'] != 'copy')
		if lvl['title'] == 'sections':
			lvl_state['section'] = lvl_state.get('section', 0)+1
		elif lvl['title'] == 'list':
			print >>fout, indented_str(lvl, lvl_state, '\\begin{enumerate}')
		elif lvl['title'] == 'bullets':
			print >>fout, indented_str(lvl, lvl_state, '\\begin{itemize}')
		elif lvl['title'] == 'mm':
			print >>fout, indented_str(lvl, lvl_state, '$$')
		elif lvl['title'] == 'm':
			print >>fout, indented_str(lvl, lvl_state, '$')
		elif lvl['title'] == 'table':
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
	def end_lvl(lvl, lvl_state):
		if lvl['title'] == 'sections':
			lvl_state['section'] = lvl_state.get('section', 0)-1
		elif lvl['title'] == 'list':
			print >>fout, indented_str(lvl, lvl_state, '\\end{enumerate}')
		elif lvl['title'] == 'bullets':
			print >>fout, indented_str(lvl, lvl_state, '\\end{itemize}')
		elif lvl['title'] == 'mm':
			print >>fout, indented_str(lvl, lvl_state, '$$')
		elif lvl['title'] == 'm':
			print >>fout, indented_str(lvl, lvl_state, '$')
		elif lvl['title'] == 'table':
			print >>fout, indented_str(lvl, lvl_state, '\\end{tabular}')
			if lvl_state.get('has_group', False):
				print >>fout, indented_str(lvl, lvl_state, '\\endgroup')
		elif lvl['title'] == 'tex':
			print >>fout, indented_str(lvl, lvl_state, '\\end{identity}')
	def process_nodes_recurse(node, indent_content):
		lvl_state = node['lvl_state']
		begin_lvl(node, lvl_state, indent_content)
		for cn in node['children']:
			begin_line(node, cn, lvl_state)
			if cn['title'] == '':
				do_line(node, cn, lvl_state)
			process_nodes_recurse(cn, lvl_state['indent_content'])
			end_line(node, cn, lvl_state)
		end_lvl(node, lvl_state)
	process_nodes_recurse(root_node, True)

largv = sys.argv
main()
