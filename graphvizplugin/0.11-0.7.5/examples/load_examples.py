#! /usr/bin/env python


import sys
import os
from trac.admin.console import TracAdmin


def main(trac_env, examples_dir='.'):
    loaded = False
    admin = TracAdmin()
    admin.env_set(trac_env)
    for file in os.listdir(examples_dir):
        if 'GraphvizExamples' in file:
            admin._do_wiki_import(os.path.join(examples_dir, file), 
                                  file.replace('%2F', '/'))
            loaded = True

    if not loaded:
        print 'The %(examples_dir)s does not contain any GrapgvizExamples files.' % locals()


if __name__ == '__main__':
    argv_len = len(sys.argv)
    if argv_len == 2:
        main(sys.argv[1])
    elif argv_len == 3:
        main(sys.argv[1], sys.argv[2])
    else:
        print 'usage: load_examples.py trac_env_path [examples_directory]'
        sys.exit(1)
