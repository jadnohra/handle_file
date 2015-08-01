import os,sys,subprocess
g_dbg = '-dbg' in sys.argv or False

def handle_generic(fp,fn,fe):
	print 'Unknown extension for [{}]'.format(fp)
def extract_command_multiline(fp,comt):
	started = False; exec_cmd = [];
	with open(fp, "r") as ifile:
		lines = [x.rstrip().strip() for x in ifile.readlines()]
		for line in lines:
			if started or line.startswith(comt[0]):
				exec_cmd.append(line if started else line[len(comt[0]):])
				started = True
				if comt[1] in exec_cmd[-1]:
					exec_cmd[-1] = exec_cmd[-1].split(comt[1])[0]
					break
	#print '>>>', exec_cmd
	return ''.join(exec_cmd)
def extract_command_singleline(fp,comt):
	exec_cmd = [];
	with open(fp, "r") as ifile:
		lines = [x.rstrip().strip() for x in ifile.readlines()]
		for line in lines:
			if line.startswith(comt):
				exec_cmd.append(line[len(comt):])
			else:
				if len(exec_cmd):
					break
	return ''.join(exec_cmd)
def extract_command(fp,comt):
	return extract_command_singleline(fp, comt) if len(comt) == 1 else extract_command_multiline(fp, comt)
def handle_embed_command(fp,fn,fe,comt):
	exec_cmd = extract_command(fp, comt)
	if len(exec_cmd):
		if g_dbg:
			print 'exec_cmd = [{}]'.format(exec_cmd)
		sys.stdout.flush()
		print 'running ...'; sys.stdout.flush()
		os.chdir(os.path.dirname(fp))
		pop = subprocess.Popen(exec_cmd.split())
		pop.wait()
		print 'done'
	else:
		print 'No command found for [{}]'.format(fp)
def handle_md(fp,fn,fe):
	handle_embed_command(fp,fn,fe,('<!---','-->'))
def handle_tex(fp,fn,fe):
	handle_embed_command(fp,fn,fe,('%'))

k_ext_handlers = {'.md': handle_md, '.tex': handle_tex}
fp,(fn,fe) = sys.argv[1], os.path.splitext(sys.argv[1])
if g_dbg:
	print 'fp,(fn,fe) = ', fp,(fn,fe)
k_ext_handlers.get(fe, handle_generic)(fp,fn,fe)
