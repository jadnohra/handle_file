##lualatex handle_file_jgr.tex
%% lualatex handle_file_jgr.tex
<%
import sys
import csv

def read_data(ifp):
	thms = []; links = []; thm = [];
	with open(ifp, 'rb') as csvfile:
		for row in csv.reader(csvfile, delimiter=' ', quotechar="'", escapechar="\\"):
			#print row
			if '->' in row:
				lnk_from = []; lnk_to = []
				lnk_ar = lnk_from
				for x in row:
					if x == '->':
						lnk_ar = lnk_to
					else:
						lnk_ar.append(x)
				links.append([lnk_from, lnk_to])
			else:
				for x in row:
					thm.append(x)
			if len(thm) == 4:
				thms.append(thm); thm = [];
	return thms,links
def break_txt(line, n = 48):
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
	return " \\\ ".join(lines)
def break_lines(lines, n = 48):
	lines = lines.split("\n")
	return " \\\ ".join([break_txt(x, n) for x in lines])
%>
<%
arg_list = '-list' in sys.argv
arg_grow = 'right' if ('-grow' not in sys.argv) else sys.argv[sys.argv.index('-grow')+1]
arg_style = 'descr' if ('-style' not in sys.argv) else sys.argv[sys.argv.index('-style')+1]
arg_box = '-box' in sys.argv
arg_thick = '-thick' in sys.argv
in_thms = []; in_links = [];
arg_ifp = 'lp_proofs.csv' if ('-in' not in sys.argv) else sys.argv[sys.argv.index('-in')+1]
if len(arg_ifp):
	in_thms, in_links = read_data(arg_ifp)
%>
% if arg_list:
	\documentclass[border=0.5cm,varwidth]{standalone}
% else:
	\documentclass[border=0.5cm]{standalone}
% endif
\usepackage{amssymb}
\usepackage{tikz}
\usetikzlibrary{graphdrawing}
\usetikzlibrary{arrows}
\usetikzlibrary{graphs}
\usetikzlibrary{decorations.pathmorphing}
\usegdlibrary{force, layered, trees}
%%\usepackage[active, tightpage]{preview}
\begin{document}
%%\begin{preview}
<%def name="gen_descr(thms)">
	\begin{description}
	% for thm in thms:
	\item[${thm[2]}] \hfill \\ ${('({}) '.format(thm[1]) if thm[1] else '')+thm[3]}
	% endfor
	\end{description}
</%def>
<%def name="gen_graph_body(thms, links, style='label')">
% 	for thm in thms:
% 		if style == 'descr':
	${thm[0]}/{${break_lines(thm[3])}};
% 		elif style == 'label':
	${thm[0]}/{${thm[2]}};
% 		endif
% 	endfor
% 	for lp in links:
% 		for lp0 in lp[0]:
% 			for link in lp[1]:
	${lp0} -> ${link};
% 			endfor
% 		endfor
% 	endfor
</%def>
%%\rule{\textwidth}{1pt}\newline\newline
<%def name="gen_graph(thms, links, style='label')">
\tikzset{grow'=${arg_grow}}
%	if arg_box:
\tikzset{every node/.style={draw}}
%	endif
%	if arg_thick:
\tikzset{every path/.style={draw, thick}}
%	endif
\tikz \graph [layered layout, nodes = {align=left}]
{
<%	gen_graph_body(thms, links, style)	%>
};
</%def>
<%
if arg_list:
	gen_descr(in_thms)
else:
	gen_graph(in_thms, in_links, arg_style)
%>
%%\end{preview}
\end{document}
