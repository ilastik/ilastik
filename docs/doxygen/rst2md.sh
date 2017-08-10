#! /bin/bash

cd ../
cp *.rst ./doxygen/mds
cd doxygen/mds
#take all the names of the index.rst file
array=`cat index.rst | grep ".. toctree::" -A 100 | grep "Indices and tables" -B 100 | head -n -2 | tail -n +3`

Output="allInOne.md"
rm index.rst
echo "" > $Output
for filename in $array
do
#	extension="${filename##*.}"
#	filename="${filename%.*}"
#	echo $filename
	pandoc --read=rst ${filename}.rst --write=markdown --output=${filename}.md --standalone
	cat ${filename}.md >> $Output
done
