''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on githab)
Version:
    '1.0.4 2015-12-15'
'''

from .cd_keys_report import Command as CommandRLS

RLS  = CommandRLS()
class Command:
	def run(self):  return RLS.run()
