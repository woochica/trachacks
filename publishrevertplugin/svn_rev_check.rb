#!/usr/bin/ruby -w

result = `svn info #{ARGV[0]}`
result =~ /Revision: (\d+)/
p $1