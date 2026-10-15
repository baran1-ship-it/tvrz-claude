#!/bin/sh
cd /home/claude/work
while kill -0 872 2>/dev/null; do sleep 20; done
for n in dub_mlady dub_stredni dub_stary lipa_mlada lipa_stredni $(awk '{print $3}' kere_fronta.txt); do
  python3 bush_far.py $n > logfar_$n.txt 2>&1; grep -h FAR logfar_$n.txt
done
echo FARREDO DONE
