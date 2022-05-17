#!/bin/ksh

file=$1
date
while [ ! -f ${file} ] ; do sleep 5 ; done

size1=`ls -l ${file} | awk '{ print $5 }'`
sleep 2
size2=`ls -l ${file} | awk '{ print $5 }'`
if [ $size1 = "" ]; then size1=0 ; fi
if [ $size2 = "" ]; then size2=1 ; fi

while [ $size1 != $size2 ]; do
   sleep 5
   date
   size1=${size2}
   size2=`ls -l ${file} |  awk '{print $5}'`
done
date
exit  0
