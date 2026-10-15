cd /home/claude/chars
python3 outfit.py muz prosivanice > log_out_muz.txt 2>&1 && echo "OUT muz ok" || echo "OUT muz FAIL"
python3 char_render.py muz_prosivanice.blend prev/muz_o2 32 cela,cela_zad,portret > log_ro_muz.txt 2>&1 && echo "REND muz ok" || echo "REND muz FAIL"
