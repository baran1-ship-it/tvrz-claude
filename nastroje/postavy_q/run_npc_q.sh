cd /home/claude/chars/q
S=/tmp/claude-0/-home-claude/fefc9bc1-d519-5e66-b949-6be759161eea/scratchpad
mkdir -p export2/npc
run() {
  n=$1
  python3 -I q_postava.py -- $n $S/qd_$n.jpg > log_d_$n.txt 2>&1 || { echo "F postava $n"; return; }
  python3 -I q_export2.py -- $n $S/qd_$n.blend export2/npc > log_e2_$n.txt 2>&1 || { echo "F export $n"; return; }
  echo "$n $(grep -o '"oblecena_trojuhelniky": [0-9]*' log_e2_$n.txt)"
}
for n in npc_sedlak npc_kovar npc_mestan; do run $n & done; wait
for n in npc_stary npc_mladik npc_selka; do run $n & done; wait
for n in npc_babka npc_divka npc_mestka; do run $n & done; wait
rm -f export2/npc/_*.blend
echo HOTOVO
