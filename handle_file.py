import os,sys,subprocess,shutil
g_dbg = '-dbg' in sys.argv or False

try:
	import mako.template as mako_temp
except ImportError:
	mako_temp = None
	pass

def handle_generic(fp,fn,fe):
	print 'Unknown extension for [{}]'.format(fp)
def extract_command_multiline(fp,comt):
	started = False; exec_cmds = []; exec_cmd = [];
	with open(fp, "r") as ifile:
		lines = [x.rstrip().strip() for x in ifile.readlines()]
		for line in lines:
			if started or line.startswith(comt[0]):
				if line != "":
					exec_cmd.append(line if started else line[len(comt[0]):])
				else:
					exec_cmds.append(exec_cmd); exec_cmd = [];
				started = True
				if comt[1] in exec_cmd[-1]:
					exec_cmd[-1] = exec_cmd[-1].split(comt[1])[0]
					break
	if len(exec_cmd):
		exec_cmds.append(exec_cmd)
	#print '>>>', exec_cmd
	return [''.join(x) for x in exec_cmds]
def extract_command_singleline(fp,comt):
	exec_cmds = []; exec_cmd = [];
	with open(fp, "r") as ifile:
		lines = [x.rstrip().strip() for x in ifile.readlines()]
		for line in lines:
			if line.startswith(comt):
				if line != comt:
					exec_cmd.append(line[len(comt):])
				else:
					exec_cmds.append(exec_cmd); exec_cmd = [];
			else:
				if len(exec_cmds)+len(exec_cmd) > 0:
					break
	if len(exec_cmd):
		exec_cmds.append(exec_cmd)
	return [''.join(x) for x in exec_cmds]
def extract_command(fp,comt):
	return extract_command_singleline(fp, comt[0]) if len(comt) == 1 else extract_command_multiline(fp, comt)
def exe_command(fp, exec_cmds, is_shell = False):
	if g_dbg and len(exec_cmds) > 1:
		print '{} cmds'.format(len(exec_cmds))
	for exec_cmd in exec_cmds:
		if len(exec_cmd):
			if g_dbg:
				print 'exec_cmd = [{}]'.format(exec_cmd)
			sys.stdout.flush()
			print 'running ...'; sys.stdout.flush()
			os.chdir(os.path.dirname(fp))
			pop = subprocess.Popen(exec_cmd.split(), shell = is_shell)
			pop.wait()
			print 'done'
		else:
			print 'No command found for [{}]'.format(fp)
def handle_embed_command(fp,fn,fe,comt):
	exec_cmd = extract_command(fp, comt)
	exe_command(fp, exec_cmd)
def handle_md(fp,fn,fe):
	handle_embed_command(fp,fn,fe,['<!---','-->'])
def handle_tex(fp,fn,fe):
	handle_embed_command(fp,fn,fe,['%'])
def handle_graphviz(fp,fn,fe):
	handle_embed_command(fp,fn,fe,['//'])
def handle_python(fp,fn,fe):
	handle_embed_command(fp,fn,fe,['#'])
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
	hfp = os.path.realpath(__file__)
	os.chdir(os.path.dirname(hfp))
	if os.path.isdir('temp') == False:
		os.mkdir('temp')
	tfiles = ['handle_file_jgr.tex.mako']
	for tf in tfiles:
		shutil.copy(tf, os.path.join('temp',tf))
	sys.argv.append('-in'); sys.argv.append(fp);
	sys.argv.append('-list')
	for aa in range(2):
		if aa == 1:
			sys.argv.remove('-list')
		_fp = os.path.join(os.path.dirname(hfp), os.path.join('temp', tfiles[0])); (_fn,_fe) = os.path.splitext(_fp);
		handle_mako(_fp, _fn, _fe)
		os.chdir(os.path.dirname(fp))
		shutil.copy(_fp.replace(".tex.mako", ".pdf"), "{}_{}{}".format(fn,aa+1,".pdf" ))
def handle_shell(fp,fn,fe):
	exe_command(fp, ['./'+os.path.basename(fp)], True)
def do_handle():
	k_ext_handlers = {'.md': handle_md, '.tex': handle_tex, '.gv': handle_graphviz
		, '.py': handle_python, '.sh': handle_shell, '.mako': handle_mako
		, '.jgr': handle_jgr}
	fp,(fn,fe) = sys.argv[1], os.path.splitext(sys.argv[1])
	if g_dbg:
		print 'fp,(fn,fe) = ', fp,(fn,fe)
	k_ext_handlers.get(fe, handle_generic)(fp,fn,fe)

do_handle()
