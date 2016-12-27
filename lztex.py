import sys, subprocess, os, math, os.path, traceback, time, shutil
import urllib, urllib2, urlparse
import re
try:
	#import urllib2.urlparse
	import requests
	import lxml
	import lxml.html
	import lxml.cssselect
except ImportError:
	lxml = None

gPrintCol = [ 'default', 'black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'bdefault', 'bblack', 'bred', 'bgreen', 'byellow', 'bblue', 'bmagenta', 'bcyan', 'bwhite'  ]
gPrintColCode = [ "\x1B[0m", "\x1B[30m", "\x1B[31m", "\x1B[32m", "\x1B[33m", "\x1B[34m", "\x1B[35m", "\x1B[36m", "\x1B[37m",
"\x1B[49m", "\x1B[40m", "\x1B[41m", "\x1B[42m", "\x1B[43m", "\x1B[44m", "\x1B[45m", "\x1B[46m", "\x1B[47m", ]
gAltCols = [ gPrintCol.index(x) for x in ['default', 'yellow'] ]
def vt_coli(coli):
	coli = coli % len(gPrintCol)
	code = gPrintColCode[coli]
	sys.stdout.write(code)
	#sys.stdout.write('\x1B[{}D'.format(len(code)-3))
def vt_col(col):
	vt_coli(gPrintCol.index(col))

def fpjoin(aa):
	ret = os.path.join(aa[0], aa[1])
	for a in aa[2:]:
	 	ret = os.path.join(ret,a)
	return ret
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
def randfilename(dir, pre, ext):
	i = 1
	while True:
		fname = "{}{}.{}".format(pre, i, ext)
		if (os.path.isfile(os.path.join(dir, fname)) == False):
			return fname
		i=i+1
def fileSize(num, suffix='b'):
	for unit in ['','K','M','G','T','P','E','Z']:
	    if abs(num) < 1024.0:
	        return "%3.1f %s%s" % (num, unit, suffix)
	    num /= 1024.0
	return "%.1f %s%s" % (num, 'Y', suffix)
def long_substr(data):
	substr = ''
	if len(data) > 1 and len(data[0]) > 0:
		for i in range(len(data[0])):
			for j in range(len(data[0])-i+1):
				if j > len(substr) and is_substr(data[0][i:i+j], data):
					substr = data[0][i:i+j]
	return substr
def is_substr(find, data):
	if len(data) < 1 and len(find) < 1:
		return False
	for i in range(len(data)):
		if find not in data[i]:
			return False
	return True
def hash_str_12(s):
	return abs(hash(s)) % (10 ** 12)
def textSearchPdfDjvu(path, phrase):
	fname_, fext = os.path.splitext(path); fext = fext.lower();
	if (fext.lower() == '.pdf'):
		args = ['pdftotext', '\"{}\"'.format(path), '-', '|', 'grep', '\"{}\"'.format(phrase)]
	elif (fext.lower() == '.djvu'):
		args = ['djvutxt', '\"{}\"'.format(path), '|', 'grep', '\"{}\"'.format(phrase)]
	else:
		return ([],[])
	#print ' '.join(args)
	proc = subprocess.Popen(' '.join(args), stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
	(out, err) = proc.communicate()
	elines = []; lines = [];
	if (len(err)):
		elines = [' ' + x.strip() for x in err.split('\n') if (len(x.strip()))]
	lines = [x.strip() for x in out.split('\n') if (len(x.strip()))]
	return (elines, lines)
def content_to_pdf(content, pdf):
	pop_in = ['node', fpjoinhere(['npm', 'arg_to_pdf.js']), '"{}"'.format(content), pdf]
	#print ' '.join(pop_in)
	pop = subprocess.Popen(' '.join(pop_in), shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = pop.communicate()
	if err and len(err):
		print err
		return False
	return True
def url_to_pdf(url, pdf, delay = None):
	if False:
		pop_in = ['wkhtmltopdf', '-q', '' if delay is None else '--javascript-delay {}'.format(int(delay*1000)), '"{}"'.format(url), pdf]
	else:
		pop_in = ['node', fpjoinhere(['npm', 'url_to_pdf.js']), '"{}"'.format(url), pdf]
	#print ' '.join(pop_in)
	pop = subprocess.Popen(' '.join(pop_in), shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = pop.communicate()
	if err and len(err):
		print err
		return False
	return True
def url_download(url, fp):
	try:
		response = urllib2.urlopen(url)
		file = open(fp, 'w')
		file.write(response.read())
		file.close()
		return True
	except:
		print ' Error'
	return False
def process_scrape(arg):
	if lxml == None:
			print "You need to install 'lxml' and 'requests' first."
			return
	mktemp()
	temps = []
	#try to get main page as pdf
	src_pdf_fp = fpjoinhere(['temp', 'scrape_source.pdf'])
	print ' Converting {} -> {} ...'.format(arg, src_pdf_fp)
	if url_to_pdf(arg, src_pdf_fp):
		temps.append(src_pdf_fp)
	else:
		print '  Failed to convert source page'
	urllib.URLopener.version = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36 SE 2.X MetaSr 1.0'
	print ' Reading \n  {} ...'.format(arg), ;sys.stdout.flush();
	page = requests.get(arg)
	dom =  lxml.html.fromstring(page.text)
	selAnchor = lxml.cssselect.CSSSelector('a')
	foundElements = selAnchor(dom)
	#print [e.get('href') for e in foundElements if e.get('href') and e.get('href').endswith('.pdf')]
	foundPdf = [e.get('href') for e in foundElements if e.get('href') and e.get('href').endswith('.pdf')]
	#print foundPdf
	print ' [{} files]'.format(len(foundPdf)); sys.stdout.flush();
	print ' Downloading {} files...'.format(len(foundPdf))
	for pdf in foundPdf:
		fn = urllib2.urlparse.urlsplit(pdf).path.split('/')[-1]
		fp = fpjoinhere(['temp', fn])
		furl = urlparse.urljoin(arg, pdf).replace('\\', '/')
		print '  {} -> {} ...'.format(furl,  fp),; sys.stdout.flush();
		if (os.path.isfile(fp)):
			print ' (cached)',
		else:
			urllib.urlretrieve(furl, fp)
		temps.append(fp)
		print '[{}]'.format(fileSize(os.path.getsize(fp)))
	return temps
def quote_list(items):
	return [x if (x.startswith("''") or x.startswith('"')) else '"{}"'.format(x) for x in items]
def join_files(files):
	fname_substr = long_substr(files)
	if len(fname_substr) and (os.path.isdir(fname_substr) == False):
		out_name = '{}.pdf'.format(fname_substr)
	else:
		out_dir = fname_substr if os.path.isdir(fname_substr) else fptemp()
		out_name = fpjoin([out_dir, randfilename(out_dir, 'join_', 'pdf')])
	pop_in = [fpjoinhere(['concat_pdf']), '--output', out_name] + quote_list(files)
	pop = subprocess.Popen(' '.join(pop_in), shell = True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = pop.communicate()
	return out_name
def move_tabs_to_new_window():
	scpt = """
	tell application "Safari"
	set l to tabs of window 1 where index >= (get index of current tab of window 1)
	make new document
	repeat with t in (reverse of l)
		move t to beginning of tabs of window 1
	end repeat
	delete tab -1 of window 1
	end tell
	"""
	args = []
	p = subprocess.Popen(['osascript', '-'] + args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	out,err = p.communicate(scpt)
	#print (p.returncode, stdout, stderr)
def get_list_tabs_field(field, right_of_curr = False):
	scpt_templ = """
	set all_urls to ""
	tell application "Safari"
		set l to tabs of window 1 {}
		repeat with t in l
			set url_str to (_FIELD_ of t) as string
			set all_urls to all_urls & url_str & "\n"
		end repeat
	end tell
	return all_urls
	""".format('where index >= (get index of current tab of window 1)' if right_of_curr else '')
	scpt = scpt_templ.replace('_FIELD_', field)
	args = []
	p = subprocess.Popen(['osascript', '-'] + args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	out,err = p.communicate(scpt)
	urls = [x for x in out.split('\n') if len(x)]
	return urls
def get_list_tabs(fields = ['URL'], right_of_curr = False):
	ret = []
	for f in fields:
		ret.append(get_list_tabs_field(f, right_of_curr))
	return ret[0] if len(fields) ==  1 else ret
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
def ask_yes(question):
	var = raw_input('{} '.format(question))
	return var in ['y', 'yes']
def list_tabs(cmd_text, right_of_curr = False):
	if 'href' in cmd_text:
		urls_titles = get_list_tabs(['URL', 'name'], right_of_curr)
		urls_titles = zip(urls_titles[0], urls_titles[1])
		print '\n', '\n'.join(['\\href{{ {} }}{{ {} }}'.format(tex_escape(x[0]), tex_escape(x[1])) for x in urls_titles]), '\n'
	else:
		use_tex = 'tex' in cmd_text
		urls = get_list_tabs(['URL'], right_of_curr)
		print '\n', '\n'.join(['\\url{{ {} }}'.format(tex_escape(x)) if use_tex else x for x in urls]), '\n'
def join_tabs(right_of_curr = False, interactive = False, TOC_only = False):
	def url_to_pdf_2(url, pdf):
		return url_to_pdf(url, pdf, 2)
	def rem_proto(url):
		return url[url.index('://')+len('://'):] if '://' in url else url
	def cached_get_url(url, ext):
		hsh = str(hash_str_12(url))
		temp_fp = fpjoin([fptemp(), hsh+ext])
		cache_fp = fpjoin([fptemp(), hsh+ext+'.cache.txt'])
		is_cached = False
		if os.path.isfile(temp_fp):
			curl = ''
			if os.path.isfile(cache_fp):
				with open(cache_fp,'r') as f:
					curl = f.read()
			if curl == url:
				return (True, temp_fp, cache_fp)
			else:
				#new_fp = fpjoin([fptemp(), randfilename(fptemp(), 'join_tab_', ext[1:])])
				return (False, temp_fp, cache_fp)
		return (False, temp_fp, cache_fp)
	def cache_register(url, cache_fp):
		with open(cache_fp,'w') as f:
			f.write(url)
	def cached_process(show_orig, orig_url, url, ext, get_lambda, temps, descr, col):
		if show_orig:
			vt_col('red'); print ' {}'.format(orig_url),;
		if descr and len(descr):
			vt_col(col); print ' [{}]'.format(descr),;
		cached, temp_fp, cache_fp = cached_get_url(url, ext)
		vt_col('white'); print ' -> [{}]'.format(temp_fp),;
		if cached:
			vt_col('magenta'); print ' (cache)';
		else:
			print '';
		vt_col('default')
		if cached:
			temps.append(temp_fp)
		else:
			if get_lambda(url, temp_fp):
				temps.append(temp_fp)
				cache_register(url, cache_fp)
	urls = get_list_tabs(right_of_curr)
	mktemp()
	temps = []
	print ''
	title_content = '<html><body> <center><b>{}</b></center> <ol> {} </ol></body></html>'.format(time.ctime(), ''.join('<li>{}</li>'.format(x) for x in urls))
	cached_process(True, 'T.O.C', title_content, '.pdf', lambda x,y: content_to_pdf(x, y), temps, None, None)
	if TOC_only:
		return
	urli = 0
	for url in urls:
		print ' {}.'.format(urli+1),; urli = urli+1;
		try:
			detected = False
			if not detected:
				if '.stackexchange.com' in url:
					url2 = rem_proto(url)
					dot_splt = url2.split('.')
					stack_topic = dot_splt[0]
					sl_splt = url2.split('/')
					if 'questions' in sl_splt:
						quest_ind = sl_splt.index('questions')
						if quest_ind >= 0 and quest_ind+1 < len(sl_splt):
							stack_number = sl_splt[quest_ind+1]
							detected = True
							pdf_url = 'http://www.stackprinter.com/export?question={}&service={}.stackexchange'.format(stack_number, stack_topic)
							cached_process(False, url, pdf_url, '.pdf', lambda x,y: url_to_pdf_2(x, y), temps, 'stack-exch:{}:{}'.format(stack_topic, stack_number), 'green')
				if 'mathoverflow.net' in url:
					url2 = rem_proto(url)
					sl_splt = url2.split('/')
					if 'questions' in sl_splt:
						quest_ind = sl_splt.index('questions')
						if quest_ind >= 0 and quest_ind+1 < len(sl_splt):
							stack_number = sl_splt[quest_ind+1]
							detected = True
							pdf_url = 'http://www.stackprinter.com/export?question={}&service=mathoverflow'.format(stack_number)
							cached_process(False, url, pdf_url, '.pdf', lambda x,y: url_to_pdf_2(x,y), temps, 'math-over:{}'.format(stack_number), 'yellow')
				if url.endswith('.pdf'):
					detected = True
					pdf = url.split('/')[-1]; pdf_url = url;
					cached_process(False, url, pdf_url, '.pdf', lambda x,y: url_download(x, y), temps, 'pdf', 'blue')
			if not detected:
				cached_process(True, url, url, '.pdf', lambda x,y: url_to_pdf_2(x,y), temps, 'webpage', 'cyan')
		except KeyboardInterrupt:
			vt_col('default')
			return
		except:
			traceback.print_exc()
	vt_col('default')
	print ''
	#print temps
	if interactive and not ask_yes('Should I join these files?'):
		return
	print join_files(temps)
def process(text_):
	patts = []
	def new_patt(name, ext = None):
		patts.append([name, ext, '{} [{}]'.format(name, ext) if ext else name ]); return name;
	text = text_.strip()
	patt1 = new_patt('find files with ')
	patt2 = new_patt('find files named ')
	patt3 = new_patt('find duplicates')
	patt4 = new_patt('join files named ', 'interactive')
	patt5 = new_patt('show ')
	patt6 = new_patt('count files')
	patt7 = new_patt('scrape and join ')
	patt8 = new_patt('scrape ')
	patt9 = new_patt('move tabs')
	patt10 = new_patt('list all tabs', 'tex')
	patt11 = new_patt('list tabs', 'tex')
	patt12 = new_patt('join tabs', 'interactive')
	patt12_1 = new_patt('toc tabs')
	patt13 = new_patt('clean temp')
	patt14 = new_patt('git status')
	patt15 = new_patt('push git', 'message')
	if text.startswith(patt1):
		arg = text[len(patt1):]
		pop_in = ['grep', '-ril', '"{}"'.format(arg), '.']
		pop = subprocess.Popen(' '.join(pop_in), shell = True, stdout=subprocess.PIPE)
		out, err = pop.communicate()
		print out
	elif text.startswith(patt2):
		arg = text[len(patt2):]
		head,tail = os.path.split(arg); head = '.' if len(head) == 0 else head;
		pop_in = ['find', head, '-maxdepth', '1', '-iname', '"*{}*"'.format(tail)]
		pop = subprocess.Popen(' '.join(pop_in), shell = True, stdout=subprocess.PIPE)
		out, err = pop.communicate()
		print out
	elif text.startswith(patt3):
		pop_in = ['fdupes', '.']
		pop = subprocess.Popen(' '.join(pop_in), shell = True, stdout=subprocess.PIPE)
		out, err = pop.communicate()
		print out
	elif text.startswith(patt4):
		arg = text[len(patt4):]
		interactive = False
		if arg.strip().endswith('interactive'):
			interactive = True
			arg = arg[:-1-len('interactive')].strip()
		head,tail = os.path.split(arg); head = '.' if len(head) == 0 else head;
		pop_in = ['find', head, '-maxdepth', '1', '-iname', '"*{}*"'.format(tail)]
		pop = subprocess.Popen(' '.join(pop_in), shell = True, stdout=subprocess.PIPE)
		out, err = pop.communicate()
		files = [x for x in sorted(out.split('\n')) if len(x)]
		if len(files):
			if interactive:
				print 'Found:'
				print '\n'.join([' '+ x for x in files])
				if not ask_yes('Should I join these files?'):
					return
			print join_files(files)
		else:
			print 'No files could be matched to [{}]'.format(tail)
	elif text.startswith(patt5):
		arg = text[len(patt5):]
		if arg.endswith('.txt'):
			pop_in = ['cat', arg]
			pop = subprocess.Popen(' '.join(pop_in), shell = True)
			pop.wait()
			print ''
		else:
			pop_in = ['open', '-a', 'Preview.app', arg]
			subprocess.Popen(' '.join(pop_in), shell = True)
	elif text.startswith(patt6):
		pop_in = ['find', '.', '-type', 'f', '-maxdepth', '1']
		pop = subprocess.Popen(' '.join(pop_in), shell = True, stdout=subprocess.PIPE)
		out, err = pop.communicate()
		print len([x for x in out.split('\n') if x.strip() != ''])
	elif text.startswith(patt7):
		arg = text[len(patt7):]
		temps = process_scrape(arg)
		print ' Joining ...'
		print '  {}'.format(join_files(temps))
	elif text.startswith(patt8):
		arg = text[len(patt8):]
		process_scrape(arg)
	elif text.startswith(patt9):
		move_tabs_to_new_window()
	elif text.startswith(patt10):
		list_tabs(text, False)
	elif text.startswith(patt11):
		list_tabs(text, True)
	elif text.startswith(patt12):
			join_tabs(True, 'interactive' in text)
	elif text.startswith(patt12_1):
			join_tabs(True, False, True)
	elif text.startswith(patt13):
		shutil.rmtree(fptemp())
	elif text.startswith(patt14):
		pop_in = ['git', 'status']
		pop = subprocess.Popen(' '.join(pop_in), shell = True)
		pop.communicate()
	elif text.startswith(patt15):
		arg = text[len(patt15):].strip()
		print arg
		pop_in = ['git', 'add', '*']; pop = subprocess.Popen(' '.join(pop_in), shell = True); pop.communicate();
		pop_in = ['git', 'commit', '-m', '"{}"'.format('trivial' if len(arg)==0 else arg)]; pop = subprocess.Popen(' '.join(pop_in), shell = True); pop.communicate();
		pop_in = ['git', 'push', 'origin', 'master']; pop = subprocess.Popen(' '.join(pop_in), shell = True); pop.communicate();
	else:
		print "Apologies, I could not understand what you said."
		print "I understand:"
		print '\n'.join([' ' + x[2] for x in patts])

process(' '.join(sys.argv[1:]))
