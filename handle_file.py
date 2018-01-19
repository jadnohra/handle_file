import os,sys,subprocess,shutil,time,traceback,fileinput
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
def break_txt(line, n = 48, endl = '\n'):
	delims = [' ', ',', ';', '.']
	lines = []
	while len(line):
	 for i in range(len(line)):
	  if line[i] in delims or i+1 == len(line):
		word = line[:i+1]; line = line[i+1:]
		if len(lines) > 0 and (len(lines[-1])+len(word) <= n or (word[-1] != ' ' and lines[-1][-1] == ' ') ):
		  lines[-1] = lines[-1] + word
		else:
		  lines.append(word.lstrip())
		break
	return endl.join(lines)
def break_lines(lines, n = 48, endl = '\n'):
	lines = lines.split("\n")
	return endl.join([break_txt(x, n, endl) for x in lines])
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
	outs = []
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
			if capture:
				out, err = pop.communicate()
				outs.append([out, err])
			else:
				pop.wait()
			if print_run:
				print 'done'
		else:
			if capture:
				outs.append(['',''])
			print 'No command found for [{}]'.format(fp)
	return outs
def do_jbu_hook(fp,fn,fe,exec_cmd):
	for line in exec_cmd:
		if len(line) and ('-[' in line or ']->' in line):
			handle_jbu_lines(fp,fn,fe, exec_cmd)
			return True
	return False
def handle_embed_command(fp,fn,fe,comt,dflt_cmd=[]):
	exec_cmd = extract_command(fp, comt)
	exec_cmd = exec_cmd if len(exec_cmd) else dflt_cmd
	if do_jbu_hook(fp,fn,fe,exec_cmd) == False:
		exe_command(fp, exec_cmd, False, False, True)
def handle_md(fp,fn,fe):
	handle_embed_command(fp,fn,fe,['<!---','-->'])
def handle_tex(fp,fn,fe):
	handle_embed_command(fp,fn,fe,['%'])
def handle_graphviz(fp,fn,fe):
	handle_embed_command(fp,fn,fe,['//'])
def handle_multi(fp,fn,fe):
	handle_embed_command(fp,fn,fe,['--#'])
def handle_python(fp,fn,fe):
	handle_embed_command(fp,fn,fe,['#'])
def handle_lzt(fp,fn,fe):
	handle_embed_command(fp,fn,fe,['#'])
def handle_frt(fp,fn,fe):
	dflt_cmd = ['./frt_template.tex -[with {self}]-[inject]-[pdf]-[png]-> {self.}.png']
	handle_embed_command(fp,fn,fe,['%'], dflt_cmd)
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
def jbu_trace_files(files, lvl=1):
	print ''.join([' ']*lvl*2),
	for (fp, fpok) in files:
		set_vt_col('green' if fpok else 'red'); print(os.path.basename(fp)), ; set_vt_col('default');
	print ''
def jbu_check_files(files):
	return all(fpok for (fp, fpok) in files)
def jbu_check_fgroups(fgroups):
	return all(jbu_check_files(fg) for fg in fgroups)
def jbu_flatten_fgroups(fgroups):
	ifiles = []
	for fg in fgroups:
		for ifile in fg:
			ifiles.append(ifile)
	return ifiles
def jbu_gen_tmpfile(tmp_files, ext):
	return fpjoinhere(['temp', '_tmp_{}{}'.format(len(tmp_files)+1, ext)])
def do_handle(fp):
	k_ext_handlers = {'.md': handle_md, '.tex': handle_tex, '.gv': handle_graphviz
		, '.py': handle_python, '.sh': handle_shell, '.mako': handle_mako
		, '.jgr': handle_jgr, '.jbu': handle_jbu, '.lzt': handle_lzt,
		'.frt': handle_frt, '.multi': handle_multi}
	(fn,fe) = os.path.splitext(sys.argv[1])
	if g_dbg:
		print 'fp,(fn,fe) = ', fp,(fn,fe)
	if '-jbu_direct' in sys.argv:
		handle_jbu_direct(fp,fn,fe)
		return
	k_ext_handlers.get(fe, handle_generic)(fp,fn,fe)
def jbu_jgr_to_tex(args, tmp_files, fp):
	fpo = jbu_gen_tmpfile(tmp_files, '.tex'); efpo = jbu_expect(fpo);
	tmako = fpo + '.mako'
	shutil.copy(fpjoinhere(['handle_file_jgr.tex.mako']), tmako)
	try:
		with open(fpo, 'w+') as of:
			print >> of, mako_temp.Template(filename=tmako).render(my_argv=args+['-in', fp])
	except:
		 print(traceback.format_exc())
	fpo2 = [fpo, jbu_expect_check(efpo)]; tmp_files.append(fpo2); return fpo2;
def yaml_cmds(_cmds):
	try:
		cmds = _cmds; cmds[0] = cmds[0].lstrip(); cmds[-1] = cmds[-1].lstrip();
		cmds = yaml.load(''.join(cmds))
		return cmds if cmds else {}
	except:
		return {}
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
def jbu_tex_to_pdf(args, tmp_files, fp):
	fpo = jbu_gen_tmpfile(tmp_files, '.pdf');
	textool = jbu_extract_tex_tool(fp, ['%'])
	rem_arg_i = []
	for i,arg in enumerate(args):
		if arg.startswith('tool:'):
			textool = arg[len('tool:'):]
			rem_arg_i.append(i)
	for arg_i in reversed(rem_arg_i):
		args.pop(arg_i)
	exec_cmd = [' '.join([textool] + args + [fp])]
	fptoolout = repext(fp, '.pdf')
	efpo = jbu_expect(fptoolout)
	#print exec_cmd
	outs = exe_command(fp, exec_cmd, False, True)
	shutil.copy(fptoolout, fpo)
	fpo2 = [fpo, jbu_expect_check(efpo)]; tmp_files.append(fpo2);
	if fpo2[1] == False:
		print 'captured log of: [{}]'.format(exec_cmd)
		print outs[0][0]; print outs[0][1];
	return fpo2;
def jbu_dvi_to_pdf(args, tmp_files, fp):
	fpo = jbu_gen_tmpfile(tmp_files, '.pdf');
	pdftool = 'dvipdfm'
	rem_arg_i = []
	for i,arg in enumerate(args):
		if arg.startswith('tool:'):
			pdftool = arg[len('tool:'):]
			rem_arg_i.append(i)
	for arg_i in reversed(rem_arg_i):
		args.pop(arg_i)
	exec_cmd = [' '.join([pdftool, fp] + args)]
	fptoolout = repext(fp, '.pdf')
	efpo = jbu_expect(fptoolout)
	#print exec_cmd
	outs = exe_command(fp, exec_cmd, False, True)
	shutil.copy(fptoolout, fpo)
	fpo2 = [fpo, jbu_expect_check(efpo)]; tmp_files.append(fpo2);
	if fpo2[1] == False:
		print 'captured log of: [{}]'.format(exec_cmd)
		print outs[0][0]; print outs[0][1];
	return fpo2;
def jbu_ps_to_pdf(args, tmp_files, fp):
	fpo = jbu_gen_tmpfile(tmp_files, '.pdf');
	pdftool = 'ps2pdf'
	rem_arg_i = []
	for i,arg in enumerate(args):
		if arg.startswith('tool:'):
			pdftool = arg[len('tool:'):]
			rem_arg_i.append(i)
	for arg_i in reversed(rem_arg_i):
		args.pop(arg_i)
	exec_cmd = [' '.join([pdftool, fp] + args)]
	fptoolout = repext(fp, '.pdf')
	efpo = jbu_expect(fptoolout)
	#print exec_cmd
	outs = exe_command(fp, exec_cmd, False, True)
	shutil.copy(fptoolout, fpo)
	fpo2 = [fpo, jbu_expect_check(efpo)]; tmp_files.append(fpo2);
	if fpo2[1] == False:
		print 'captured log of: [{}]'.format(exec_cmd)
		print outs[0][0]; print outs[0][1];
	return fpo2;
def jbu_dvi_to_ps(args, tmp_files, fp):
	fpo = jbu_gen_tmpfile(tmp_files, '.ps');
	pdftool = 'dvips'
	rem_arg_i = []
	for i,arg in enumerate(args):
		if arg.startswith('tool:'):
			pdftool = arg[len('tool:'):]
			rem_arg_i.append(i)
	for arg_i in reversed(rem_arg_i):
		args.pop(arg_i)
	exec_cmd = [' '.join([pdftool, fp] + args)]
	fptoolout = repext(fp, '.ps')
	efpo = jbu_expect(fptoolout)
	#print exec_cmd
	outs = exe_command(fp, exec_cmd, False, True)
	shutil.copy(fptoolout, fpo)
	fpo2 = [fpo, jbu_expect_check(efpo)]; tmp_files.append(fpo2);
	if fpo2[1] == False:
		print 'captured log of: [{}]'.format(exec_cmd)
		print outs[0][0]; print outs[0][1];
	return fpo2;
def jbu_tex_to_dvi(args, tmp_files, fp):
	fpo = jbu_gen_tmpfile(tmp_files, '.dvi');
	textool = jbu_extract_tex_tool(fp, ['%'], def_tool='latex')
	rem_arg_i = []
	for i,arg in enumerate(args):
		if arg.startswith('tool:'):
			textool = arg[len('tool:'):]
			rem_arg_i.append(i)
	for arg_i in reversed(rem_arg_i):
		args.pop(arg_i)
	exec_cmd = [' '.join([textool] + args + [fp])]
	fptoolout = repext(fp, '.dvi')
	efpo = jbu_expect(fptoolout)
	# print exec_cmd
	outs = exe_command(fp, exec_cmd, False, True)
	shutil.copy(fptoolout, fpo)
	fpo2 = [fpo, jbu_expect_check(efpo)]; tmp_files.append(fpo2);
	if fpo2[1] == False:
		print 'captured log of: [{}]'.format(exec_cmd)
		print outs[0][0]; print outs[0][1];
	return fpo2;
def jbu_pdf_to_png(args, tmp_files, fp):
	fpo = jbu_gen_tmpfile(tmp_files, '.png'); efpo = jbu_expect(fpo);
	pngtool = 'convert'
	exec_cmd = [' '.join([pngtool, '-density', '300', '-alpha', 'remove', fp, fpo] + args)]
	#print exec_cmd
	exe_command(fp, exec_cmd)
	fpo2 = [fpo, jbu_expect_check(efpo)]; tmp_files.append(fpo2); return fpo2;
def jbu_pdf_to_jpeg(args, tmp_files, fp):
	fpo = jbu_gen_tmpfile(tmp_files, '.jpeg'); efpo = jbu_expect(fpo);
	pngtool = 'convert'
	exe_command(fp, [' '.join([pngtool, '-density', '300', '-alpha', 'remove', fp, fpo] + args)])
	fpo2 = [fpo, jbu_expect_check(efpo)]; tmp_files.append(fpo2); return fpo2;
def jbu_md_to_pdf(args, tmp_files, fp):
	fpo = jbu_gen_tmpfile(tmp_files, '.pdf'); efpo = jbu_expect(fpo);
	mdtool = 'pandoc'
	exe_command(fp, [' '.join([mdtool, fp, '-o', fpo] + args)])
	fpo2 = [fpo, jbu_expect_check(efpo)]; tmp_files.append(fpo2); return fpo2;
def jbu_md_to_tex(args, tmp_files, fp):
	fpo = jbu_gen_tmpfile(tmp_files, '.tex'); efpo = jbu_expect(fpo);
	mdtool = 'pandoc'
	exe_command(fp, [' '.join([mdtool, fp, '-o', fpo] + args)])
	fpo2 = [fpo, jbu_expect_check(efpo)]; tmp_files.append(fpo2); return fpo2;
def jbu_lzt_to_md(args, tmp_files, fp):
	fpo = jbu_gen_tmpfile(tmp_files, '.md'); efpo = jbu_expect(fpo);
	mdtool = fpjoinhere(['lztex'])
	exe_command(fp, [' '.join([mdtool, fp, '-o', fpo] + args)])
	fpo2 = [fpo, jbu_expect_check(efpo)]; tmp_files.append(fpo2); return fpo2;
def jbu_wrap_single(args, tmp_files, fp):
	fpo = jbu_gen_tmpfile(tmp_files, os.path.splitext(fp)[1]); efpo = jbu_expect(fpo);
	wrap_n = int(args[0]) if len(args) else 48
	lines = []
	with open(fp, 'r') as ifp:
		lines = ifp.readlines()
	text = break_lines(''.join(lines).replace(' \n', ' ').replace('\n ', ' ').replace('\n', ''), wrap_n)
	with open(fpo, 'w') as ofp:
		ofp.write(text)
	fpo2 = [fpo, jbu_expect_check(efpo)]; tmp_files.append(fpo2); return fpo2;
def jbu_concat_pdf(args, tmp_files, fgroups):
	fgo = []
	for files in fgroups:
		fpo = jbu_gen_tmpfile(tmp_files, '.pdf')
		efpo = jbu_expect(fpo)
		concattool = fpjoinhere(['concat_pdf'])
		ifiles = [x[0] for x in files if x[1]]
		exe_command(fpo, [' '.join([concattool, '--output', fpo]+ifiles)], True)
		fpo = [[fpo, jbu_expect_check(efpo)]]; tmp_files.append(fpo);
		fgo.append(fpo)
	return fgo
def jbu_wrap(args, tmp_files, fgroups):
	fgo = []
	for files in fgroups:
		fpo = []
		for (fp, fpok) in files:
			if fpok:
				fpo.append(jbu_wrap_single(args, tmp_files, fp))
			else:
				fpo.append(['', False])
		fgo.append(fpo)
	return fgo
def jbu_to_tex(args, tmp_files, fgroups):
	fgo = []
	for files in fgroups:
		fpo = []
		for (fp, fpok) in files:
			if fpok:
				if fp.endswith('.tex'):
					fpo.append([fp, fpok])
				if fp.endswith('.md'):
					fpo.append(jbu_md_to_tex(args, tmp_files, fp))
				if fp.endswith('.jgr'):
					fpo.append(jbu_jgr_to_tex(args, tmp_files, fp))
			else:
				fpo.append(['', False])
		fgo.append(fpo)
	return fgo
def jbu_to_md(args, tmp_files, fgroups):
	fgo = []
	for files in fgroups:
		fpo = []
		for (fp, fpok) in files:
			if fpok:
				if fp.endswith('.md'):
					fpo.append([fp, fpok])
				if fp.endswith('.lzt'):
					fpo.append(jbu_lzt_to_md(args, tmp_files, fp))
			else:
				fpo.append(['', False])
		fgo.append(fpo)
	return fgo
def jbu_to_png(args, tmp_files, fgroups):
	fgo = []
	for files in fgroups:
		fpo = []
		for (fp, fpok) in files:
			if fpok:
				if fp.endswith('.png'):
					fpo.append([fp, fpok])
				elif fp.endswith('.pdf'):
					fpo.append(jbu_pdf_to_png(args, tmp_files, fp))
			else:
				fpo.append(['', False])
		fgo.append(fpo)
	return fgo
def jbu_to_jpeg(args, tmp_files, fgroups):
	fgo = []
	for files in fgroups:
		fpo = []
		for (fp, fpok) in files:
			if fpok:
				if fp.endswith('.jpeg'):
					fpo.append([fp, fpok])
				if fp.endswith('.pdf'):
					fpo.append(jbu_pdf_to_jpeg(args, tmp_files, fp))
			else:
				fpo.append(['', False])
		fgo.append(fpo)
	return fgo
def jbu_to_pdf(args, tmp_files, fgroups):
	fgo = []
	for files in fgroups:
		fpo = []
		for (fp, fpok) in files:
			if fpok:
				if fp.endswith('.pdf'):
					fpo.append([fp, fpok])
				elif fp.endswith('.jgr'):
					(tex, texok) = jbu_jgr_to_tex(args, tmp_files, fp)
					if texok:
						fpo.append(jbu_tex_to_pdf(args, tmp_files, tex))
					else:
						fpo.append(['', False])
				elif fp.endswith('.lzt'):
					(md, mdok) = jbu_lzt_to_md(args, tmp_files, fp)
					if mdok:
						fpo.append(jbu_md_to_pdf(args, tmp_files, md))
					else:
						fpo.append(['', False])
				elif fp.endswith('.tex'):
					fpo.append(jbu_tex_to_pdf(args, tmp_files, fp))
				elif fp.endswith('.dvi'):
					fpo.append(jbu_dvi_to_pdf(args, tmp_files, fp))
				elif fp.endswith('.ps'):
					fpo.append(jbu_ps_to_pdf(args, tmp_files, fp))
				elif fp.endswith('.md'):
					fpo.append(jbu_md_to_pdf(args, tmp_files, fp))
			else:
				fpo.append(['', False])
		fgo.append(fpo)
	return fgo
def jbu_to_dvi(args, tmp_files, fgroups):
	fgo = []
	for files in fgroups:
		fpo = []
		for (fp, fpok) in files:
			if fpok:
				if fp.endswith('.dvi'):
					fpo.append([fp, fpok])
				elif fp.endswith('.jgr'):
					(tex, texok) = jbu_jgr_to_tex(args, tmp_files, fp)
					if texok:
						fpo.append(jbu_tex_to_dvi(args, tmp_files, tex))
					else:
						fpo.append(['', False])
				elif fp.endswith('.tex'):
					fpo.append(jbu_tex_to_dvi(args, tmp_files, fp))
			else:
				fpo.append(['', False])
		fgo.append(fpo)
	return fgo
def jbu_to_ps(args, tmp_files, fgroups):
	fgo = []
	for files in fgroups:
		fpo = []
		for (fp, fpok) in files:
			if fpok:
				if fp.endswith('.ps'):
					fpo.append([fp, fpok])
				elif fp.endswith('.dvi'):
					fpo.append(jbu_dvi_to_ps(args, tmp_files, fp))
			else:
				fpo.append(['', False])
		fgo.append(fpo)
	return fgo
def jbu_fail_files():
	return [['', False]]
def jbu_fail_fgo():
	return [jbu_fail_files()]
def jbu_include_tex(fo, args, cfg, tmp_files, files):
	arg_recipe = '' if ('-recipe' not in args) else args[args.index('-recipe')+1]
	pre_recipe = cfg.get(arg_recipe, r"{\includegraphics[]{jbu_1}}")
	if fo[1]:
		fpo = jbu_gen_tmpfile(tmp_files, '.tex')
		shutil.copy(fo[0], fpo)
		#print 'fpo', fpo, files
		for line in fileinput.input(fpo, inplace=1):
			if '\end{document}' not in line:
				print line,
			else:
				for fpi in [x[0] for x in files if x[1]]:
					if fpi.endswith('.pdf'):
						recipe = pre_recipe.replace('jbu_1', fpi)
						print recipe
				print line,
		tmp_files.append([fpo, True])
		return [[fpo, True]]
	else:
		return jbu_fail_files()
def jbu_include(args, cfg, tmp_files, fgroups):
	fgo = []
	if len(fgroups) != 2:
		return jbu_fail_fgo()
	for fo in fgroups[0]:
		if fo[0].endswith('.tex'):
			fgo.append(jbu_include_tex(fo, args, cfg, tmp_files, fgroups[1]))
		else:
			fgo.append(jbu_fail_files)
	return fgo
def jbu_inject_tex(fo, args, cfg, tmp_files, files):
	def read_inject_content(fp):
		lines = []
		with open(fp, "r") as ifile:
			lines = ifile.readlines()
		rem_indices = []
		for index in sorted(rem_indices, reverse=True):
			lines.pop(index)
		return ''.join(lines)
	arg_recipe = '' if ('-recipe' not in args) else args[args.index('-recipe')+1]
	pre_recipe = cfg.get(arg_recipe, r"jbu_1")
	if fo[1]:
		fpo = jbu_gen_tmpfile(tmp_files, '.tex')
		shutil.copy(fo[0], fpo)
		#print 'fpo', fpo, files
		for line in fileinput.input(fpo, inplace=1):
			if '\end{document}' not in line:
				print line,
			else:
				for fpi in [x[0] for x in files if x[1]]:
					recipe = pre_recipe.replace('jbu_1', read_inject_content(fpi))
					print recipe
				print line,
		tmp_files.append([fpo, True])
		return [[fpo, True]]
	else:
		return jbu_fail_files()
def jbu_inject(args, cfg, tmp_files, fgroups):
	fgo = []
	if len(fgroups) != 2:
		return jbu_fail_fgo()
	for fo in fgroups[0]:
		if fo[0].endswith('.tex'):
			fgo.append(jbu_inject_tex(fo, args, cfg, tmp_files, fgroups[1]))
		else:
			fgo.append(jbu_fail_files)
	return fgo
def jbu_with(args, ctx, fgroups):
	with_groups = jbu_parse_fgroups(ctx, ' '.join(args))
	return fgroups + with_groups
def jbu_dict(args, ctx, fgroups):
	ctx['file_dict'][args[0]] = fgroups
	return fgroups
def jbu_handle(cmd, ctx, fgroups):
	args = cmd.split()[1:]
	if cmd.strip() == '':
		return fgroups
	elif cmd.split()[0] == 'tex':
		return jbu_to_tex(args, ctx['tmp_files'], fgroups)
	elif cmd.split()[0] == 'md':
		return jbu_to_md(args, ctx['tmp_files'], fgroups)
	elif cmd.split()[0] == 'latex':
		return jbu_to_latex(args, ctx['tmp_files'], fgroups)
	elif cmd.split()[0] == 'pdf':
		return jbu_to_pdf(args, ctx['tmp_files'], fgroups)
	elif cmd.split()[0] == 'dvi':
		return jbu_to_dvi(args, ctx['tmp_files'], fgroups)
	elif cmd.split()[0] == 'ps':
		return jbu_to_ps(args, ctx['tmp_files'], fgroups)
	elif cmd.split()[0] == 'png':
		return jbu_to_png(args, ctx['tmp_files'], fgroups)
	elif cmd.split()[0] == 'jpeg':
		return jbu_to_jpeg(args, ctx['tmp_files'], fgroups)
	elif cmd.split()[0] == 'with':
		return jbu_with(args, ctx, fgroups)
	elif cmd.split()[0] == 'dict':
		return jbu_dict(args, ctx, fgroups)
	elif cmd.split()[0] == 'concat':
		return jbu_concat_pdf(args, ctx['tmp_files'], fgroups)
	elif cmd.split()[0] == 'include':
		return jbu_include(args, ctx['cfg'], ctx['tmp_files'], fgroups)
	elif cmd.split()[0] == 'inject':
		return jbu_inject(args, ctx['cfg'], ctx['tmp_files'], fgroups)
	elif cmd.split()[0] == 'wrap':
		return jbu_wrap(args, ctx['tmp_files'], fgroups)
	return jbu_fail_fgo()
def jbu_parse_line(fvars,line):
	if line.lstrip().startswith('#'):
		return ([],[line])
	for (k,v) in fvars.items():
		line = line.replace(k,v)
	delims = [' -[', ']-[', ']->']
	line_parts = [[]]; orig_parts = [[]]
	while len(line):
		for i in range(len(line)):
			el = (i+1 == len(line))
			if (len(line[i:])>=3 and line[i:i+3] in delims) or (el):
				word = line.strip() if el else line[:i].strip(); delim = '' if el else line[i:i+3]; line = '' if el else line[i+3:];
				oword = word + delim
				line_parts[-1].append(word); line_parts.append([]);
				orig_parts[-1].append(oword); orig_parts.append([]);
				break
	return (line_parts[:-1], orig_parts[:-1])
def jbu_parse_fgroups(ctx, text):
	groups = text.split(' and ')
	fgo = []
	for g in groups:
		flist = [x.strip() for x in g.split(',')]
		gin_files = []
		for fi in flist:
			if fi in ctx['file_dict']:
				gin_files.extend( jbu_flatten_fgroups( ctx['file_dict'][fi] ) )
			else:
				afp = to_afp(ctx['base'], fi); files = [[afp, os.path.isfile(afp)]];
				gin_files.extend(files)
		fgo.append(gin_files)
	return fgo
def jbu_exec_part(ctx, cmd, cmd_i, cmd_n):
	#print 'cmd', cmd
	cmd_res = 0
	if cmd_i == 0:
		in_fgroups = jbu_parse_fgroups(ctx, cmd)
		ctx['stack_fgroups'].append(in_fgroups)
		cmd_res = 1 if jbu_check_fgroups(ctx['stack_fgroups'][-1]) else 0
	elif cmd_i+1 < cmd_n:
		in_fgroups = ctx['stack_fgroups'].pop()
		out_fgroups = jbu_handle(cmd, ctx, in_fgroups)
		cmd_res = 1 if jbu_check_fgroups(out_fgroups) else 0
		ctx['stack_fgroups'].append(out_fgroups)
	else:
		out_fgroups = ctx['stack_fgroups'].pop()
		cmd_res = 1 if jbu_check_fgroups(out_fgroups) else 0
		if cmd.startswith('!') or ('.' not in cmd):
			ctx['file_dict'][cmd] = out_fgroups
			#print 'dict', cmd, out_fgroups
		else:
			if len(out_fgroups) == 1 and out_fgroups[0][0][1] == True:
				shutil.copy(out_fgroups[0][0][0], to_afp(ctx['base'], cmd))
				cmd_res = 3
			else:
				cmd_res = 2
	return cmd_res
def find_jbu_yaml_lines(lines):
	in_yaml = False; yaml_lines = [];
	li = 0
	for line in lines:
		if in_yaml or line.strip() == '---':
			if line.strip() == '...':
				in_yaml = False
			else:
				if in_yaml:
					yaml_lines.append(li)
				in_yaml = True
		li = li+1
	return yaml_lines
def handle_jbu(base, fvars, lines, use_yaml = True):
	cmd_res_cols = ['red', 'green', 'magenta', 'cyan']
	mktemp()
	chains = []
	yaml_cfg = {}
	if use_yaml:
		yaml_lines = [lines[x] for x in find_jbu_yaml_lines(lines)]
		yaml_cfg = yaml.load(''.join(yaml_lines))
		if yaml_cfg:
			jbu_lines = yaml_cfg.get('jbu', '').split('\n')
		else:
			yaml_cfg = {}
			jbu_lines = lines
	else:
		jbu_lines = lines
	for line in [x.strip() for x in jbu_lines if len(x.strip())]:
		chains.append(jbu_parse_line(fvars,line.strip()))
	tmp_files = []; file_dict = {}; stack_fgroups = [];
	ctx = {'base':base, 'tmp_files':tmp_files, 'file_dict':file_dict, 'stack_fgroups':stack_fgroups, 'cfg':yaml_cfg }
	for (chain, ochain) in chains:
		ctx['with_files'] = []
		if len(chain):
			for pi in range(len(chain)):
				cmd = ' '.join(chain[pi])
				cmd_res = jbu_exec_part(ctx, cmd, pi, len(chain))
				set_vt_col(cmd_res_cols[cmd_res]); print ' '.join(ochain[pi]), ; set_vt_col('default');
				sys.stdout.flush()
			print ''
		else:
			print ochain[0]
	print ''
	for (k,v) in file_dict.items():
		print '{}:'.format(k),
		pp = [(x[0], x[1]) for x in jbu_flatten_fgroups(file_dict[k])]
		for p in pp:
			set_vt_col('default' if p[1] else 'red'); print "'{}' ".format(p[0]);
		set_vt_col('default')
def handle_jbu_lines(fp,fn,fe,lines, use_yaml = True):
	fvars = {}
	fvars['{self}'] = os.path.basename(fp)
	fvars['{self.}'] = os.path.splitext(os.path.basename(fp))[0]
	base = os.path.dirname(fp)
	handle_jbu(base, fvars, lines, use_yaml)
def handle_jbu_direct(fp,fn,fe):
	line = ' '.join(sys.argv[sys.argv.index('-jbu_direct')+1:])
	handle_jbu_lines(fp,fn,fe,[line], False)
def handle_jbu_file(fp,fn,fe):
	lines = []
	with open(fp, "r") as ifile:
		lines = ifile.readlines()
	handle_jbu_lines(base, fvars, lines)
#print sys.argv
do_handle(sys.argv[1])
