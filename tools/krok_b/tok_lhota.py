import json, math
exec(open('tok_tvrz.py').read().split("C=json.load")[0])
c=idx(700,960); pu=nahoru(c)
print('nad (700,960) pramen', pos(pu[-1]), round(H[pu[-1]],1), 'delka', len(pu)*K)
for q in pu[::10]: print('  ', tuple(round(v) for v in pos(q)), round(H[q],1), round(ACC[q]*K*K/1e4,2))
c=idx(515.7,871.9); pd=dolu(c)
print('z okraje Lhoty dolu', len(pd)*K)
for q in pd[:90:6]: print('  ', tuple(round(v) for v in pos(q)), round(H[q],1), round(ACC[q]*K*K/1e4,2))
