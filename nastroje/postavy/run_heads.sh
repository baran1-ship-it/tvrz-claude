cd /home/claude/chars
python3 char_build.py kluk 1.0 13 0.5 0.35 0.75 > log_cb_kluk.txt 2>&1
for n in muz kluk; do
 python3 head_build.py $n > log_hb_$n.txt 2>&1
 python3 char_render.py ${n}_head.blend prev/${n}_h4 48 portret,profil > log_r_$n.txt 2>&1
 echo "DONE $n"
done
