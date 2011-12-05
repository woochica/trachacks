from trac.env import Environment
import getopt, sys, os, string

# This script will attempt to update which ever recipe it finds listed (as filenames) in the project's name directory. The project
# directory should reside in the same directory as the recipe_put.py script.
# Such as:
# #~>ls
# My_Trac_Site recipe_get.py recipe_put.py
#
# Where My_Trac_Site is a directory containing the saved recipes:
# #~>ls My_Trac_Site
# 049AppsbecauseofFRAMEWORK.recipe application_001.recipe framework_before_update.recipe
#
# The name of the file denotes the name of the recipe. I am using two characters '^^' as the delimeter.
# There is practically no error checking, so be careful with path names as the like.
# I built this script to ease the burden from using the GUI to make many small changes to a growing list of bitten rules.

_USAGE = """recipe_put.py <path to Trac Environment>
"""

def readFile(file_name):
  file_obj = open(file_name, 'r')
  file_data = file_obj.read()
  file_obj.close()
  return file_data.split('^^')

def recipeFiles(trac_env):
  file_list = []
  for files in os.listdir(os.path.split(trac_env)[1] + '_recipes'):
    if string.find(files, '.recipe') != -1:
      file_list.append(str(os.path.join(os.getcwd(), os.path.split(trac_env)[1] + '_recipes', files)))
  return file_list

def commitRecipe(env, (name, path, active, recipe, min_rev, max_rev, label, description, placeholder)):
  print 'Committing to recipe:', name
  if min_rev == 'None':
    min_rev = ''
  if max_rev == 'None':
    max_rev = ''
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

def processArgs():
  try:
    opts = getopt.getopt(sys.argv[1:], '')[1]
    if opts[0][-1:] == os.sep:
      opts[0] = opts[0][:-1]

  except getopt.GetoptError:
    printUsage('Invalid arguments.')
  if not opts:
    printUsage('No options specified')
  if os.path.exists(opts[0]):
    return opts[0]
  else:
    printUsage('Trac Environment not found')

if __name__ == '__main__':
  trac_env = processArgs()
  sys.exit(0)
  env = Environment(trac_env)
  for files in recipeFiles(trac_env):
    commitRecipe(env, readFile(files))
