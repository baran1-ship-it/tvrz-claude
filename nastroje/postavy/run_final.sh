cd /home/claude/chars
b() { N=$1; B="$2"; K=$3; ENVS="$4"
env $ENVS python3 char_build.py $N $B > log_cb_$N.txt 2>&1 && echo "F $N base"
python3 head_build.py $N > log_hb_$N.txt 2>&1 && echo "F $N head"
python3 outfit.py $N $K > log_out_$N.txt 2>&1 && echo "F $N outfit"
python3 char_render.py ${N}_$K.blend prev/${N}_fin 32 portret,cela > log_rfin_$N.txt 2>&1 && echo "F $N render"
}
b muz "1.0 45 0.6 0.4 0.55" prosivanice ""
b kluk "1.0 13 0.5 0.35 0.6" zelena ""
b zena "0.0 38 0.45 0.62 0.55" satyr "CUP=0.6 FIRM=0.9"
echo F_DONE
