from trac.env import Environment
import getopt, sys, os

# This handy little script will capture all bitten recipes from the specified Trac environment
# and save them as individual files. The file name itself denotes the unique rule name identifier.
# Each column value is separated by ^^ as the delimiter.

# IMPORTANT: Do not modify the first value... ever.
#
# This script is designed to function with the recipe_put.py script located in the same directory.
# Run this script to obtain bitten rules, edit them, then run the recipe_put.py with the same arguments.
# The saved recipes will reside in a created directory with the same name as your Trac directory name appended with: _recipes

_USAGE = """recipe_get.py <path to Trac Environment>
"""

def writeFile(trac_env, file_name, (path, active, recipe, min_rev, max_rev, label, description)):
  directory = os.path.split(trac_env)[1] + '_recipes'
  if not os.path.exists(os.path.join(os.getcwd(), directory)):
    os.makedirs(os.path.join(os.getcwd(), directory))
  print 'Saving:', file_name + '.recipe', 'to', os.getcwd() + '/' + directory
  file_obj = open(os.path.join(os.getcwd(), directory, file_name + '.recipe'), 'w')
  file_obj.write(str(file_name) + '^^' + \
                 str(path) + '^^' + \
                 str(active) + '^^' + \
                 str(recipe) + '^^' + \
                 str(min_rev) + '^^' + \
                 str(max_rev) + '^^' + \
                 str(label) + '^^' + \
                 str(description) + '^^')
  file_obj.close()
                 
def fetchRecipes(trac_env):
  env = Environment(trac_env)
  db = env.get_db_cnx()
  cursor = db.cursor()
  cursor.execute("SELECT path,active,recipe,min_rev,max_rev,label,description,name FROM bitten_config")
  for row in cursor:
    (path, active, recipe, min_rev, max_rev, label, description, name) = row
    writeFile(trac_env, name, (path, active, recipe, min_rev, max_rev, label, description))
    
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
  print 'Using Trac Environment:', trac_env
  fetchRecipes(trac_env)
