#! /usr/bin/env python3
# coding: cp1251

import os
import webbrowser
import tempfile
#import sw 		as app
import cudatext as app
import json
import re

#### Release ####
app_name	= 'CudaText'
rpt_head = '''
<html>
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
	<title>{app_name} keymapping</title>
	<style type="text/css">
td, th, body {
	color: 			#000;
	font-family: 	Verdana, Arial, Helvetica, sans-serif;
	font-size: 		12px;
}
table {
	border-width: 	1px;
	border-spacing: 2px;
	border-color: 	gray;
	border-collapse:collapse;
}
table td, table th{
	border-width: 	1px;
	padding: 		1px;
	border-style: 	solid;
	border-color: 	gray;
}
td.ctg {
    font-weight: 	bold;
    color: 			darkblue;
	text-align: 	center;
}
.dbl {
	background-color: #ffb;
}
.h-btn, .h-mod {
	font-family: 	"Courier New", Courier, monospace;
	font-size: 		12px;
	font-weight: 	bold;
}
table#dbls td:nth-child(1) {
	text-align: 	right;
}
table#cmds td:nth-child(2) {
	text-align: 	right;
}
table.akeys td:nth-child(1) {
	text-align: 	center;
}
table.compact td {
	text-align: 	center;
}
table.compact td:nth-child(1) {
	text-align: right;
}
	</style>
</head>
<body>
'''.replace('{app_name}', app_name)
rpt_foot = '''
</body>
</html>
'''

def do_report(fn):
	srs_dlm	= icase( app_name=='CudaText', ' * '
					,app_name=='SynWrite', ' � '
					,'')
	# Collect data
	mods	= ['', 'Shift', 'Ctrl', 'Shift+Ctrl', 'Alt', 'Shift+Alt', 'Ctrl+Alt', 'Shift+Ctrl+Alt']
	btnsFn	= ["Esc", "Tab", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"]
	btnsIns	= ["Ins", "Del", "BkSp", "Enter", "Space", "Home", "End", "PgUp", "PgDn", "Left", "Right", "Up", "Down"]
	btnsNum	= icase( app_name=='CudaText',
			  ["NumDiv", "NumMul", "NumMinus", "NumPlus", "NumDot"
			  ,"Num0", "Num1", "Num2", "Num3", "Num4", "Num5", "Num6", "Num7", "Num8", "Num9"]
					,app_name=='SynWrite',
			  [			 "Num *",  "Num -",    "Num +",   "Num Del"
			  ,"Num0", "Num1", "Num2", "Num3", "Num4", "Num5", "Num6", "Num7", "Num8", "Num9"]
					,[''])
	btnsDig	= ["`", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "="]
	btnsLtrQ= ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]"]
	btnsLtrA= ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "\\"]
	btnsLtrZ= ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"]
	btns	= btnsFn + btnsIns + btnsNum + btnsDig + btnsLtrQ + btnsLtrA + btnsLtrZ
	keys2nms= {}
	has_series = False
	dblkeys = []
	ctgs	= []
	cmdinfos= []

	n=0
	while True:
		# Cud (5	  ,'smth', 'Shift+Ctrl+F1', 'Alt+Q * Ctrl+T')
		# Syn (5,'ctg','smth', 'Shift+Ctrl+F1', 'Alt+Q � Ctrl+T')
		cmdinfo = app.app_proc(app.PROC_GET_COMMAND, str(n))
		n += 1
		if cmdinfo is None: break
		if cmdinfo[0]<=0: continue
		if app_name=='CudaText':
			# Add default category
			cmdinfo	= ('Commands', cmdinfo[1], cmdinfo[2], cmdinfo[3])
		else:
			cmdinfo	= (cmdinfo[1], cmdinfo[2], cmdinfo[3], cmdinfo[4])

		ctg, name, keys1, keys2 = cmdinfo
		if	name.startswith('lexer:'):		continue	# ?? lexer? smth-more?
		if (app_name=='CudaText' and
			name.startswith('plugin:')):	continue	# ?? plugin? smth-more?
		if (app_name=='SynWrite' and
			ctg=='Plugin'):
			cmdinfo	= (ctg, 'Plugin: '+name, keys1, keys2)

		cmdinfos += [cmdinfo]
	if app_name=='CudaText':
		cmdinfos = add_cud_plugins(cmdinfos, 'plugin: ', 'Plugins')

	for ctg, name, keys1, keys2 in cmdinfos:
		if ctg not in ctgs:
			ctgs += [ctg]
		for keys in (keys1, keys2):
			if not keys: continue
			if srs_dlm in keys:
				# Series: Alt+Q * Ctrl+T
				# It will be parsed later when all single keys are done
				has_series = True
				continue # see Repeat...
			else:
				btn	= ('+'+keys).split('+')[-1]					# 'B' 			 	from 'Shift+Ctrl+B'
				save_btn_mod_name(
					btn
				,	keys[:-len(btn)].rstrip('+')				# 'Shift+Ctrl'		from 'Shift+Ctrl+B'
				,	name, keys
				,	mods, btns, keys2nms, dblkeys
				)

	# Repeat to parse series
	for ctg, name, keys1, keys2 in cmdinfos:
		for keys in (keys1, keys2):
			if srs_dlm not in keys: continue
			# Series: Alt+Q * Ctrl+T
			# 1. Check a conflict with head
			#	(Alt+)(Q)
			keys_hd  = keys.split(srs_dlm)[0]					# 'Alt+Q'			from 'Alt+Q * Ctrl+T'
			if keys_hd in keys2nms:
				# Conflict!
				dblkeys 			+= [keys_hd]
				keys2nms[keys_hd]	+= [name]
			# 2. Save as
			#	(Alt+Q * Ctrl+)(T)
			btn	= ('+'+keys.split(srs_dlm)[-1]).split('+')[-1]	# 'T' 				from 'Alt+Q * Ctrl+T' or 'Alt+Q * T'
			save_btn_mod_name(
				btn
			,	keys[:-len(btn)].rstrip('+')					# 'Alt+Q * Ctrl'	from 'Alt+Q * Ctrl+T'
			,	name, keys
			,	mods, btns, keys2nms, dblkeys
			)

	# Fill reports
	acmd_ank	= '<a name="all-cmds"/>All commands'
	acmd_ref	= '<a href="#all-cmds">All commands</a>'
	akeys_ank	= '<a name="all-keys"/>All keys with full command names'
	akeys_ref	= '<a href="#all-keys">All keys</a>'
	skeys_ank	= '<a name="ser-keys"/>All series-keys'
	skeys_ref	= '<a href="#ser-keys">All series-keys</a>'
	ckeys_ank	= '<a name="compact"/>All keys, compact view'
	ckeys_ref	= '<a href="#compact">Compact keys</a>'
	dbl_good	= '<a name="dbls"/>No conflicts'
	dbl_fail	= '<a name="dbls"/>Conflicts'
	dbl_ref		= '<a href="#dbls">Conflicts</a>'
	c_cmd		= 'Command'
	c_cmds		= 'Commands'
	c_key		= 'Keys'
	c_keys		= 'Keys'
	c_btn		= 'Button'
	with open(fn, 'w', encoding='utf8') as f:
		f.write(rpt_head)

		# Conflicts
		if not dblkeys:
			f.write('<h2>{}</h2>\n'.format(dbl_good))
		else:
			f.write('<h2>{}</h2>\n'.format(dbl_fail))
			f.write('<table id="dbls">\n')
			f.write(	'<tr><th class="h-key">{}</th>\n\t<th class="h-cmd">{}</th></tr>\n'.format(c_key, c_cmds))
			for keys in dblkeys:
				f.write('<tr><td{cls}>{ks}</td>			\n\t<td{cls}>{nms}</td>		</tr>\n'.format(
						cls=' class="dbl"'
					   ,ks=keys
					   ,nms='\n\t<br/>'.join(keys2nms[keys])
				))
			f.write('</table><br/>\n')

		# All cmds
		f.write('<h2>{ank} ({akeys}, {ckeys})</h2>\n'.format(ank=acmd_ank, akeys=akeys_ref, ckeys=ckeys_ref))
		if 1<len(ctgs):
			for i_ctg, ctg in enumerate(ctgs):
				f.write('<a href="#ctg{}">{}</a>{}\n'.format(i_ctg, ctg, ' |' if (1+i_ctg)<len(ctgs) else ''))
			f.write('<p>\n')
		f.write('<table id="cmds" width="600">\n')
		f.write('<tr><th class="h-cmd">{}</th><th class="h-key">{}</th></tr>\n'.format(c_cmd, c_keys))
		for i_ctg, ctg_chp in enumerate(ctgs):
			if ctg_chp:
				f.write('<tr><td class="ctg" colspan=2> <a name="ctg{}">{}</td></tr>\n'.format(i_ctg,  ctg_chp))
			for ctg, name, keys1, keys2 in cmdinfos:
				if not ctg == ctg_chp: continue
				has_dbl		= False
				cnt			= 0
				twokeys		= []
				for keys in (keys1, keys2):
					cnt			+= (1 if keys else 0)
					if keys in dblkeys:
						has_dbl	= True
						twokeys	+= ['<span class="dbl">{}</span>'.format(keys)]
					else:
						twokeys	+= [keys]
				f.write('<tr><td{cls}>{nm}</td>\n\t<td>{twks}</td></tr>\n'.format(
						cls=(' class="dbl"' if has_dbl else '')
					   ,nm=name
					   ,twks=('<br/>' if cnt==2 else '').join(twokeys)))
		f.write('</table><br/>\n')

		# All keys
		f.write('<h2>{} ({}, {})</h2>\n'.format(akeys_ank, acmd_ref, ckeys_ref))
		if has_series:
			f.write('{}\n'.format(skeys_ref))
		for with_series in (False, True):
			if with_series and not has_series: continue
			if not has_series:
				mods_wo	= 				  mods
			elif with_series:
				mods_wo	= [mod for mod in mods if (		srs_dlm in mod)]
			else:
				mods_wo	= [mod for mod in mods if (not	srs_dlm in mod)]

			# 1. Without series
			# 2. Only with series
			if has_series and with_series:
				f.write('<h3>{}\n</h3>'.format(skeys_ank))
			f.write('<table class="akeys">\n')
			f.write('<tr><th></th>\n\t<th class="h-mod">'+('</th>\n\t<th class="h-mod">'.join(mods_wo))+'</th></tr>\n')
			for btn in btns:
				filled	= False
				for mod in mods_wo:
					keys = keys4mod_btn(mod, btn)
					if keys in keys2nms:
						filled	= True
						break
				if not filled: continue
				f.write('<tr><td class="h-btn">'+btn+'</td>\n')
				for mod in mods_wo:
					keys = keys4mod_btn(mod, btn)
					names= keys2nms.get(keys, '')
					if not names:
						f.write('\t<td></td>\n')
					else:
						f.write('\t<td{cls}>{txt}</td>\n'.format(
								cls=icase(keys in dblkeys, ' class="dbl"'									, '')
							   ,txt=icase(name, '<a title="{}">{}</a>'.format(keys, '<br/>'.join(names))	, '')
					))
				f.write('</tr>\n')
			f.write('</table><br/>\n')

		# Compact
		f.write('<h2>{} ({}, {})</h2>\n'.format(ckeys_ank, acmd_ref, akeys_ref))
		compact_view(f, keys2nms, dblkeys, mods, btnsFn)
		compact_view(f, keys2nms, dblkeys, mods, btnsIns)
		compact_view(f, keys2nms, dblkeys, mods, btnsNum, True)
		compact_view(f, keys2nms, dblkeys, mods, btnsDig, True, True)
		compact_view(f, keys2nms, dblkeys, mods, btnsLtrQ, True, True)
		compact_view(f, keys2nms, dblkeys, mods, btnsLtrA, True, True)
		compact_view(f, keys2nms, dblkeys, mods, btnsLtrZ, True, True)

		f.write(rpt_foot)

def 	compact_view(f, keys2nms, dblkeys, mods, btns, skip_no_mod=False, skip_sh_mod=False):
	f.write('<table class="compact">\n')
	f.write('<tr><th></th>\n\t<th class="h-btn">'+('</th>\n\t<th class="h-btn">'.join(btns))+'</th></tr>\n')
	for mod in mods:
		if skip_no_mod and 0==len(mod)	: continue
		if skip_sh_mod and mod=='Shift'	: continue
		f.write('<tr><td class="h-mod">'+mod+'</td>\n')
		for btn in btns:
			keys = keys4mod_btn(mod, btn)
			names= keys2nms.get(keys, '')
			f.write('\t<td{cls}>{txt}</td>\n'.format(
					cls=icase(keys in dblkeys, ' class="dbl"'
							, '')
				   ,txt=icase(names, '<a title="{}\n({})">{}</a>'.format(
								  '\n'.join(names).replace('"', "'")
								, keys
								, ''.join((icase(name.startswith('plugin:'), 'P', 'C') for name in names)) )
							, '')
			))
		f.write('</tr>\n')
	f.write('</table><br/>\n')

def save_btn_mod_name(btn, mod, name, keys, mods, btns, keys2nms, dblkeys):
	if mod not in mods:
		mods += [mod]
	if btn not in btns:
		btns += [btn]
	if keys in keys2nms:
		# Conflict!
		dblkeys 		+= [keys]
		keys2nms[keys]	+= [name]
	else:
		keys2nms[keys] 	=  [name]

def keys4mod_btn(mod, btn):
	if not mod:
		return btn
	if mod[-1]==' ':
		# "Ctrl+Q * " "Q"
		return mod + btn
	# "Ctrl+Q * Ctrl" "Q"
	return mod + '+' + btn

def add_cud_plugins(cmdinfos, prfx, ctg):
	# {"commands":{
	# 	"grp":{
	#		"0":{"caption":"***", "hotkey":"***"},
	#		"1":{"caption":"***", "hotkey":"***"},
	#	},
	# }}
	plugs_json	= os.path.join(app.app_path(app.APP_DIR_SETTINGS), 'plugins.json')
	plugs		= json_loads(open(plugs_json).read())
	for nums in plugs["commands"].values():
#		pass;				print('len(nums)={}'.format(len(nums)))
		for dct_plug in nums.values():
#			pass;			print('len(dct_plug)={}'.format(len(dct_plug)))
#			if 'hotkey' in dct_plug:
#				pass;		print('plug={}'.format(dct_plug['caption']))
			cap		= dct_plug['caption']
			cmdinfos += [(ctg, prfx+cap, dct_plug.get('hotkey', ''), '')]
	return cmdinfos

#### Main ####
class Command:
	def run(self):
		if app_name=='CudaText' and app.app_api_version()<'1.0.105':
			app.msg_box('Plugin needs newer app version', app.MB_OK)
			return

		htm_file = os.path.join(tempfile.gettempdir(), '{}_keymapping.html'.format(app_name))
		do_report(htm_file)
		webbrowser.open_new_tab('file://'+htm_file)
		app.msg_status('Opened browser with file '+htm_file)

#### Utils ####
def json_loads(s, **kw):
	''' Adapt s for json.loads
			Delete comments
			Delete unnecessary ',' from {,***,} and [,***,]
	'''
	s	= re.sub('//.*'		, ''	, s)
	s	= re.sub('{\s*,'	, '{'	, s)
	s	= re.sub(',\s*}'	, '}'	, s)
	s	= re.sub('\[\s*,'	, '['	, s)
	s	= re.sub(',\s*\]'	, ']'	, s)
	return json.loads(s, **kw)

def icase(*pars):
	""" Params	cond1,val1[, cond2,val2, ...[, valElse]...]
		Result	Value for first true cond in pairs otherwise last odd param or None
		Examples
			icase(1==2,'a', 3==3,'b') == 'b'
			icase(1==2,'a', 3==4,'b', 'c') == 'c'
			icase(1==2,'a', 3==4,'b') == None
	"""
	for ppos in range(1,len(pars),2) :
		if pars[ppos-1] :
			return pars[ppos]
	return pars[-1] if 1==len(pars)%2 else None
	#def icase

#######################################################
if __name__ == '__main__':
	pass;						print('OK')

""" TODO
"""