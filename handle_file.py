import os,sys,subprocess
g_dbg = '-dbg' in sys.argv or False

def handle_generic(fp,fn,fe):
	print 'Unknown extension for [{}]'.format(fp)
def handle_md(fp,fn,fe):
	started = False; exec_cmd = [];
	with open(fp, "r") as ifile:
		lines = [x.rstrip().strip() for x in ifile.readlines()]
		for line in lines:
			if started or line.startswith('<!---'):
				started = True
				exec_cmd.append(line.replace('<!---', ''))
				if '-->' in exec_cmd[-1]:
					exec_cmd[-1] = exec_cmd[-1].split('-->')[0]
					break
	if len(exec_cmd):
		exec_cmd = ''.join(exec_cmd)
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

k_ext_handlers = {'.md': handle_md}
fp,(fn,fe) = sys.argv[1], os.path.splitext(sys.argv[1])
if g_dbg:
	print 'fp,(fn,fe) = ', fp,(fn,fe)
k_ext_handlers.get(fe, handle_generic)(fp,fn,fe)
