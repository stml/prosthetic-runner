# Copyright (C) 2011 Philter Phactory Ltd.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE X
# CONSORTIUM BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# Except as contained in this notice, the name of Philter Phactory Ltd. shall
# not be used in advertising or otherwise to promote the sale, use or other
# dealings in this Software without prior written authorization from Philter
# Phactory Ltd..
#

"""this file is a utility for distributed development - rather than checking
app.yaml into version control and having all developers edit it themselves,
leaving to version control conflicts, this script will build a local app.yaml
from a template file and a local settings file.


"""


from __future__ import with_statement
import re,sys,os
import datetime

# open up app.yaml,and replace the application and version lines with
# the ones we have from the command line
app_file = os.path.join(os.path.dirname(__file__), "app.yaml")
template_file = os.path.join(os.path.dirname(__file__), "app.yaml.template")
temp_file = os.path.join(os.path.dirname(__file__), ".app.yaml.temp")
local_file = os.path.join(os.path.dirname(__file__), "app.yaml.local")


local_overrides = {}
try:
    with open(local_file) as local:
        for line in local:
            k,v = re.split(r'\s*:\s*', re.sub(r'\n','',line))
            if k and v:
                local_overrides[k] = v

except IOError:
    print "=== no app.yaml.local file found ==="
    print
    print "Please copy app.yaml.local.template to app.yaml.local and alter"
    print "for your particular environment before running manage.py."
    print
    sys.exit(1)

application = local_overrides["application"]
version = local_overrides["version"]

# allow environment override
version = os.getenv("VERSION", version)
application = os.getenv("APPLICATION", application)

print "=== building local environment: %s version %s"%(application, version)

with open(template_file) as template:
    output = open(temp_file, "w")
    for line in template:
        for key in local_overrides:
            line = re.sub(r'application: .*$', "application: %s"%application, line)
        line = re.sub(r'^version: .*$', "version: %s"%version, line)
        output.write(line)    
output.close()

# replace app.yaml atomicly. Safer.
os.rename(temp_file, app_file)


try:
    import subprocess
    pipe = os.popen("git log -n 1")
    version = pipe.readline().split()[1]
    vfile = open(os.path.join(os.path.dirname(__file__), "media/static/version.txt"), "w")
    vfile.write(version)
    vfile.write(" shipped ")
    vfile.write(str(datetime.datetime.now()))
    vfile.close()
    pipe.close()
except Exception, e:
    print "Can't write version file: %s"%e


