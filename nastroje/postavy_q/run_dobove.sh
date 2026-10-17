cd /home/claude/chars/q
S=/tmp/claude-0/-home-claude/fefc9bc1-d519-5e66-b949-6be759161eea/scratchpad
rm -rf export2; mkdir -p export2/hrdinove
for n in muz zena kluk; do
  python3 -I q_postava.py -- $n $S/qd_$n.jpg > log_d_$n.txt 2>&1 || echo "F postava $n"
  python3 -I q_export2.py -- $n $S/qd_$n.blend export2/hrdinove > log_e2_$n.txt 2>&1 || echo "F export $n"
  echo "$n $(grep -o '"oblecena_trojuhelniky": [0-9]*' log_e2_$n.txt)"
done
rm -f export2/hrdinove/_*.blend
python3 -I q_check.py -- export2/hrdinove muz,zena,kluk $S/q_check3.png > /dev/null 2>&1
ANIM=Idle_Loop FRAME=10 python3 -I q_check.py -- export2/hrdinove muz,zena,kluk $S/q_check3_idle.png > /dev/null 2>&1
echo HOTOVO
