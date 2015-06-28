me=$BASH_SOURCE
mydir=$(dirname $me)

export PYTHONPATH="$mydir/lib:$PYTHONPATH"
. $mydir/ve/bin/activate
