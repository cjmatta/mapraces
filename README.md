This is a small python wrapper around the `hadoop mfs -setace` command to simplify adding elements to access control expressions.

#### Why?

When MapR ACEs get long and complicated adding a simple user or group statement requires running `hadoop mfs -getace FILE`, copying the current expression and adding the item, this script will do that for you.

#### Usage:

```
./mapraces --help
Usage: mapraces [options]

Options:
 -h, --help            show this help message and exit
 -a, --add             Add ACE
 -d, --delete          Delete ACE
 -R                    Recursively set ACE
 --setinherit=[true|false]
                       Weather or not to aces will inherit to children
 --preservemodebits=[true|false]
                       Weather or not to preserve mode bits

 ACE Permissions:
   Set one (or more) of the following ACE permissions

   --readfile=READFILE
                       reafile ACE
   --writefile=WRITEFILE
                       writefile ACE
   --executefile=EXECUTEFILE
                       executefile ACE
   --readdir=READDIR   readdir ACE
   --addchild=ADDCHILD
                       addchild ACE
   --deletechild=DELETECHILD
                       deletechild ACE
   --lookupdir=LOOKUPDIR
                       lookupdir ACE
```

### TODO

-	Implement the `--delete` flag
-	Test with more complicated ACEs
