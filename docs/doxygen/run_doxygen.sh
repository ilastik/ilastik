#! /bin/bash

mkdir -p mds


cd ../
array=`find *.rst`
cp *.rst ./doxygen/mds
cd doxygen/mds

for filename in $array
do
	extension="${filename##*.}"
	filename="${filename%.*}"
	echo $filename
	pandoc --read=rst ${filename}.rst --write=markdown --output=${filename}.md --standalone
done
#index
#pandoc --read=rst index.rst --write=markdown --output=index.md --standalone --table-of-contents
#mv index.rst index.md 
rm *.rst

