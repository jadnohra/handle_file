#!/bin/bash
#echo "handling $1"
mydir=`dirname $0`
#echo $mydir
python $mydir/handle_file.py "$@"
