# set up the default rake task
task :default => [:build]

python24='C:\Python24\python'
python25='C:\Python25\python'
python26='C:\Python26\python'

desc 'Compiles the Python code'
task :compile do
	puts "Compiling ..."
	sh 'python compile.py'
end

desc 'Build a Python egg with the default system version'
task :build => [:compile] do
	puts "Creating Python egg ..."
	sh 'python setup.py bdist_egg'
end

desc 'Build Python eggs for all available versions'
task :buildall => [:build24, :build25, :build26]

desc 'Build a Python 2.4 egg'
task :build24 do
	puts "Creating Python 2.4 egg ..."
	sh "#{python24} setup.py bdist_egg"
end

desc 'Build a Python 2.5 egg'
task :build25 do
	puts "Creating Python 2.5 egg ..."
	sh "#{python25} setup.py bdist_egg"
end

desc 'Build a Python 2.6 egg'
task :build26 do
	puts "Creating Python 2.6 egg ..."
	sh "#{python25} setup.py bdist_egg"
end
