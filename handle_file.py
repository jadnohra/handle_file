import os,sys,subprocess,shutil,time,traceback
import yaml

g_dbg = '-dbg' in sys.argv or False
g_dbgexec = g_dbg or ('-dbgexec' in sys.argv or False)

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
def fpjoin(aa):
	ret = os.path.join(aa[0], aa[1])
	for a in aa[2:]:
	 	ret = os.path.join(ret,a)
	return ret
def to_afp(base, fp):
	return fp if os.path.isabs(fp) else fpjoin([base, fp])
def fphere():
	return os.path.dirname(os.path.realpath(__file__))
def fpjoinhere(aa):
	return fpjoin([fphere()]+aa)
def fptemp():
	return fpjoin([fphere(), 'temp'])
def cwdtemp():
	os.chdir(fptemp())
def mktemp():
	if os.path.isdir(fptemp()) == False:
		os.mkdir(fptemp())
def repext(fp, ext):
	return os.path.splitext(fp)[0]+ext
def handle_generic(fp,fn,fe):
	print 'Unknown extension for [{}]'.format(fp)
def extract_command_multiline(fp,comt):
	started = False; exec_cmd = [];
	with open(fp, "r") as ifile:
		for line in ifile.readlines():
			if started or line.startswith(comt[0]):
				if (line.strip() != comt[0]):
					exec_cmd.append(line if started else line[len(comt[0]):])
				started = True
				if len(exec_cmd) and (comt[1] in exec_cmd[-1]):
					if (exec_cmd[-1].strip() != comt[1]):
						exec_cmd[-1] = exec_cmd[-1].split(comt[1])[0]
					else:
						exec_cmd.pop()
					break
	return exec_cmd
def extract_command_singleline(fp,comt):
	exec_cmd = [];
	with open(fp, "r") as ifile:
		for line in ifile.readlines():
			if line.startswith(comt) and (line.strip() != comt or len(exec_cmd)):
				exec_cmd.append(line[len(comt):])
			else:
				if len(exec_cmd) > 0:
					break
	return exec_cmd
def extract_command(fp,comt):
	return extract_command_singleline(fp, comt[0]) if len(comt) == 1 else extract_command_multiline(fp, comt)
def exe_command(fp, exec_cmds, is_shell = False, capture = False, print_run = False):
	if g_dbgexec and len(exec_cmds) > 1:
		print '{} cmds'.format(len(exec_cmds))
	for exec_cmd in exec_cmds:
		if len(exec_cmd):
			if g_dbgexec:
				print 'exec_cmd = [{}]'.format(exec_cmd); sys.stdout.flush();
			if print_run:
				print 'running ...'; sys.stdout.flush()
			os.chdir(os.path.dirname(fp))
			pop_in = exec_cmd.split() if not is_shell else exec_cmd
			if capture or '-silence' in exec_cmd:
				pop = subprocess.Popen(pop_in, shell = is_shell, stdout=subprocess.PIPE)
			else:
				pop = subprocess.Popen(pop_in, shell = is_shell)
			pop.wait()
			if print_run:
				print 'done'
		else:
			print 'No command found for [{}]'.format(fp)
	return None
def is_jbu_command(exec_cmd):
	return len(exec_cmd) and ('-[' in exec_cmd[0] or ']->' in exec_cmd[0])
def handle_embed_command(fp,fn,fe,comt):
	exec_cmd = extract_command(fp, comt)
	if is_jbu_command(exec_cmd):
		handle_jbu_lines(fp,fn,fe,[x.rstrip() for x in exec_cmd])
		return None
	else:
		return exe_command(fp, exec_cmd, False, False, True)
def handle_md(fp,fn,fe):
	return handle_embed_command(fp,fn,fe,['<!---','-->'])
def handle_tex(fp,fn,fe):
	return handle_embed_command(fp,fn,fe,['%'])
def handle_graphviz(fp,fn,fe):
	return handle_embed_command(fp,fn,fe,['//'])
def handle_python(fp,fn,fe):
	return handle_embed_command(fp,fn,fe,['#'])
def handle_mako(fp,fn,fe):
	if mako_temp:
		os.chdir(os.path.dirname(fp))
		with open(fn, 'w+') as of:
			if g_dbg:
				print 'rendering mako to ', fn, '...'; sys.stdout.flush()
			print >> of, mako_temp.Template(filename=fp).render()
		handle_embed_command(fp,fn,fe,['##'])
	else:
		print 'Mako is not installed'
	return None
def handle_jgr(fp,fn,fe):
	return handle_embed_command(fp,fn,fe,[';'])
def handle_shell(fp,fn,fe):
	exe_command(fp, ['./'+os.path.basename(fp)], True)
def jbu_expect(fp):
	if os.path.isfile(fp):
		mt = os.path.getmtime(fp)
		os.utime(fp, (os.path.getatime(fp), mt-10))
		mt = os.path.getmtime(fp)
		return {'fp':fp, 'mt':mt }
	else:
	 	return {'fp':fp, 'mt':0}
def jbu_expect_check(exp):
	return jbu_expect(exp['fp'])['mt'] > exp['mt']
def do_handle(fp):
	k_ext_handlers = {'.md': handle_md, '.tex': handle_tex, '.gv': handle_graphviz
		, '.py': handle_python, '.sh': handle_shell, '.mako': handle_mako
		, '.jgr': handle_jgr, '.jbu': handle_jbu}
	(fn,fe) = os.path.splitext(sys.argv[1])
	if g_dbg:
		print 'fp,(fn,fe) = ', fp,(fn,fe)
	k_ext_handlers.get(fe, handle_generic)(fp,fn,fe)
def jbu_jgr_to_tex(args, fp):
	texname = 'handle_file_jgr.tex'; makoname = texname+'.mako'
	texo = fpjoin([fphere(),'temp',texname])
	tmako = fpjoin([fphere(),'temp',makoname])
	shutil.copy(fpjoinhere([makoname]), tmako)
	in_argv = args + ['-in', fp]
	#print in_argv
	etexo = jbu_expect(texo)
	try:
		with open(texo, 'w+') as of:
			print >> of, mako_temp.Template(filename=tmako).render(my_argv=in_argv)
	except:
		 print(traceback.format_exc())
	return [ [texo, jbu_expect_check(etexo)] ]
def yaml_cmds(_cmds):
	cmds = _cmds; cmds[0] = cmds[0].lstrip(); cmds[-1] = cmds[-1].lstrip();
	return yaml.load(''.join(cmds))
def jbu_extract_tools(fp, cmt):
	cmds = extract_command(fp,['%'])
	ycmds = yaml_cmds(cmds)
	if 'tools' in ycmds:
		return ycmds['tools']
	return []
def jbu_extract_tex_tool(fp, cmt, def_tool='pdflatex'):
	tools = jbu_extract_tools(fp, cmt)
	for tool in tools:
		if 'tex' in tool:
			return tool
	return def_tool
def jbu_tex_to_pdf(args, fp):
	fpo = repext(fp, '.pdf'); efpo = jbu_expect(fpo)
	textool = jbu_extract_tex_tool(fp, ['%'])
	exe_command(fp, [' '.join([textool, fp, '-interaction', 'batchmode'] + args)])
	return [ [fpo, jbu_expect_check(efpo)] ]
def jbu_md_to_pdf(args, fp):
	fpo = repext(fp, '.pdf'); efpo = jbu_expect(fpo)
	mdtool = 'pandoc'
	exe_command(fp, [' '.join([mdtool, fp, '-o', fpo] + args)])
	return [ [fpo, jbu_expect_check(efpo)] ]
def jbu_concat_pdf(args, tmp_files, files):
	fpo = fpjoinhere(['temp', '_tmp_{}{}'.format(len(tmp_files)+1, '.pdf')])
	efpo = jbu_expect(fpo)
	concattool = fpjoinhere(['concat_pdf'])
	if len(files):
		ifiles = [x[0] for x in files if x[1]]
		exe_command(fpo, [' '.join([concattool, '--output', fpo]+ifiles)], True)
	fpos = [[fpo, jbu_expect_check(efpo)]]; tmp_files.append(fpos);
	return fpos
def jbu_to_tex(args, files):
	fpo = []
	for (fp, fpok) in files:
		if fpok:
			if fp.endswith('.tex'):
				fpo.append([fp, fpok])
			if fp.endswith('.jgr'):
				fpo.extend(jbu_jgr_to_tex(args, fp))
		else:
			fpo.append(['', False])
	return fpo
def jbu_to_pdf(args, files):
	fpo = []
	for (fp, fpok) in files:
		if fpok:
			if fp.endswith('.pdf'):
				fpo.append([fp, fpok])
			elif fp.endswith('.jgr'):
				texs = jbu_jgr_to_tex(args, fp)
				#print 'texs', texs
				for (tex, texok) in texs:
					if texok:
						fpo.extend(jbu_tex_to_pdf(args, tex))
					else:
						fpo.append(['', False])
			elif fp.endswith('.tex'):
				fpo.extend(jbu_tex_to_pdf(args, fp))
			elif fp.endswith('.md'):
				fpo.extend(jbu_md_to_pdf(args, fp))
		else:
			fpo.append(['', False])
	return fpo
def jbu_handle(cmd, tmp_files, files):
	args = cmd.split()[1:]
	if cmd.strip() == '':
		return files
	elif cmd.split()[0] == 'tex':
		return jbu_to_tex(args, files)
	elif cmd.split()[0] == 'pdf':
		return jbu_to_pdf(args, files)
	elif cmd.split()[0] == 'concat':
		return jbu_concat_pdf(args, tmp_files, files)
	return [ ['', False] ]
def jbu_parse_line(fvars,line):
	if line.lstrip().startswith('#'):
		return ([],[line])
	for (k,v) in fvars.items():
		line = line.replace(k,v)
	delims = ['-[', ']-']
	line_parts = [[]]; orig_parts = [[]]
	while len(line):
		for i in range(len(line)):
			el = (i+1 == len(line))
			if (len(line[i:])>=2 and line[i:i+2] in delims) or (el):
				word = line.strip() if el else line[:i].strip(); delim = '' if el else line[i:i+2]; line = '' if el else line[i+2:];
				oword = word + delim
				if delim == '-[':
					line_parts[-1].append(word); line_parts.append([]);
					orig_parts[-1].append(oword); orig_parts.append([]);
				elif delim == ']-':
					if len(line) == 0:
						return ([],[])
					elif line[0] == '[':
						line_parts[-1].append(word); line_parts.append([]);
						orig_parts[-1].append(oword); orig_parts.append([]);
					elif line[0] == '>':
						line_parts[-1].append(word); line_parts.append([]);
						orig_parts[-1].append(oword); orig_parts.append([]);
					else:
						return [[]]
					line = line[1:]
				else:
					line_parts[-1].append(word); line_parts.append([]);
					orig_parts[-1].append('> ' + oword); orig_parts.append([]);
				break
	return (line_parts[:-1], orig_parts[:-1])
def jbu_trace_files(files, lvl=1):
	print ''.join([' ']*lvl*2),
	for (fp, fpok) in files:
		set_vt_col('green' if fpok else 'red'); print(os.path.basename(fp)), ; set_vt_col('default');
	print ''
def jbu_check_files(files):
	return all([fpok for (fp,fpok) in files])
def jbu_exec_part(base, tmp_files, file_dict, stack_files, cmd, cmd_i, cmd_n):
	#print 'cmd', cmd
	cmd_res = 0
	if cmd_i == 0:
		in_files = []
		for fi in cmd.split(','):
			if fi in file_dict:
				in_files.extend(file_dict[fi])
			else:
				afp = to_afp(base, fi); files = [[afp, os.path.isfile(afp)]];
				in_files.extend(files)
		stack_files.append(in_files)
		cmd_res = 1 if jbu_check_files(stack_files[-1]) else 0
	elif cmd_i+1 < cmd_n:
		cmd_files = stack_files.pop()
		#print 'cmd_files', cmd_files
		ofp = jbu_handle(cmd, tmp_files, cmd_files)
		cmd_res = 1 if jbu_check_files(ofp) else 0
		#print 'ofp', ofp
		tfps = []
		for (fp, fpok) in ofp:
			fe = os.path.splitext(fp)[1]
			tfp = fpjoinhere(['temp', '_tmp_{}{}'.format(len(tmp_files)+1, fe)])
			if fpok:
				shutil.copy(fp, tfp); tfps.append([tfp, True]);
			else:
				tfps.append([tfp, False]);
		tmp_files.append(tfps)
		stack_files.append(tfps)
	else:
		save_files = stack_files.pop()
		cmd_res = 1 if jbu_check_files(save_files) else 0
		if cmd.startswith('!') or ('.' not in cmd):
			file_dict[cmd] = save_files
			if g_dbg:
				print 'generated', cmd
			#print file_dict
		else:
			if g_dbg:
				print 'copying', save_files[0], '->', to_afp(base, cmd)
			if len(save_files) == 1 and save_files[0][1] == True:
				shutil.copy(save_files[0][0], to_afp(base, cmd))
				cmd_res = 3
			else:
				cmd_res = 2
	return cmd_res
def handle_jbu(base, fvars, lines):
	cmd_res_cols = ['red', 'green', 'magenta', 'cyan']
	mktemp()
	chains = []
	lines = [x.strip() for x in lines if len(x.strip())]
	for line in lines:
		chains.append(jbu_parse_line(fvars,line))
	tmp_files = []; file_dict = {}; stack_files = [];
	for (chain, ochain) in chains:
		if len(chain):
			if g_dbg:
				print 'chain', chain
			for pi in range(len(chain)):
				cmd = ' '.join(chain[pi])
				if g_dbg:
					print 'cmd', cmd
				cmd_res = jbu_exec_part(base, tmp_files, file_dict, stack_files, cmd, pi, len(chain))
				set_vt_col(cmd_res_cols[cmd_res]); print ' '.join(ochain[pi]), ; set_vt_col('default');
				sys.stdout.flush()
			print ''
		else:
			print ochain[0]
def handle_jbu_lines(fp,fn,fe,lines):
	fvars = {}
	fvars['{self}'] = os.path.basename(fp)
	fvars['{self.}'] = os.path.splitext(os.path.basename(fp))[0]
	base = os.path.dirname(fp)
	handle_jbu(base, fvars, lines)
def handle_jbu_file(fp,fn,fe):
	lines = []
	with open(fp, "r") as ifile:
		lines = ifile.readlines()
	handle_jbu_lines(base, fvars, lines)
do_handle(sys.argv[1])
