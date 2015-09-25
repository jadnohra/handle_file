##lualatex handle_file_jgr.tex
%% lualatex handle_file_jgr.tex
<%
import sys
import csv

def read_data(ifp):
	thms = []; links = []; thm = []; args = [];
	with open(ifp, 'rb') as csvfile:
		for row in csv.reader(csvfile, delimiter=' ', quotechar="'", escapechar="\\"):
			#print row
			if len(row) and row[0] == ';args':
				args = row[1:]
			else:
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
	return thms,links,args
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
in_args = {}
in_thms = []; in_links = [];
in_args['ifp'] = 'lp_proofs.csv' if ('-in' not in sys.argv) else sys.argv[sys.argv.index('-in')+1]
if len(in_args['ifp']):
	in_thms, in_links, ifp_args = read_data(in_args['ifp'])
in_argv = sys.argv + ifp_args
in_args['list'] = '-list' in in_argv
in_args['grow'] = 'right' if ('-grow' not in in_argv) else in_argv[in_argv.index('-grow')+1]
in_args['style'] = 'stmt' if ('-style' not in in_argv) else in_argv[in_argv.index('-style')+1]
in_args['box'] = '-box' in in_argv
in_args['thick'] = '-thick' in in_argv
%>
% if in_args['list']:
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
<%def name="gen_list(thms)">
	\begin{description}
	% for thm in thms:
	\item[${thm[2]}] \hfill \\ ${('({}) '.format(thm[1]) if thm[1] else '')+break_lines(thm[3],240)}
	% endfor
	\end{description}
</%def>
<%def name="gen_graph_body(thms, links, style='label')">
% 	for thm in thms:
% 		if style == 'stmt':
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
\tikzset{grow'=${in_args['grow']}}
%	if in_args['box']:
\tikzset{every node/.style={draw}}
%	endif
%	if in_args['thick']:
\tikzset{every path/.style={draw, thick}}
%	endif
\tikz \graph [layered layout, nodes = {align=left}]
{
<%	gen_graph_body(thms, links, style)	%>
};
</%def>
<%
if in_args['list']:
	gen_list(in_thms)
else:
	gen_graph(in_thms, in_links, in_args['style'])
%>
%%\end{preview}
\end{document}
