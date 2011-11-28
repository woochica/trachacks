from trac.env import Environment
import getopt, sys, os, string

# This script will attempt to update which ever recipe it finds listed (as filenames) in the current working directory
# Such as:
#
# 049AppsbecauseofMOOSE.recipe (which is what we have named the 'All Applications because of MOOSE' recipt)
#
# The name of the file denotes the name of the recipe. I am using two characters '^^' as the delimeter.
# There is practically no error checking, so be careful with path names as the like.
# I built this script to ease the burden of using the GUI to make many small changes to our growing list of bitten rules.

_USAGE = """recipe_put.py <path to Trac Environment>
"""

def readFile(file_name):
  file_obj = open(file_name, 'r')
  file_data = file_obj.read()
  file_obj.close()
  return file_data.split('^^')

def recipeFiles():
  file_list = []
  for files in os.listdir('.'):
    if string.find(files, '.recipe') != -1:
      file_list.append(files)
  return file_list

def commitRecipe(trac_env, (name, path, active, recipe, min_rev, max_rev, label, description, placeholder)):
  print 'Commiting to recipe:', name
  if min_rev == 'None':
    min_rev = ''
  if max_rev == 'None':
    max_rev = ''
  env = Environment(trac_env)
  db = env.get_db_cnx()
  cursor = db.cursor()
  cursor.execute("UPDATE bitten_config SET name=%s,path=%s,active=%s,recipe=%s,min_rev=%s,max_rev=%s,label=%s,description=%s WHERE name=%s",
                 (name, path, int(active), recipe, min_rev, max_rev, label, description, name))
  db.commit()

def printUsage(message):
  sys.stderr.write(_USAGE)
  if message:
    sys.exit('\nFATAL ERROR: ' + message)
  else:
    sys.exit(1)

def process_args():
  try:
    opts = getopt.getopt(sys.argv[1:], '')[1]
  except getopt.GetoptError:
    printUsage('Invalid arguments.')
  if not opts:
    printUsage('No options specified')
  if os.path.exists(opts[0]):
    return opts[0]
  else:
    printUsage('Trac Environment not found')

if __name__ == '__main__':
  trac_env = process_args()
  for files in recipeFiles():
    commitRecipe(trac_env, readFile(files))
