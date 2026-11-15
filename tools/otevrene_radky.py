import glob,re,os
HOT=re.compile(r"opraven|hotovo|v kódu|v datech|ověřeno|overeno|✅|vyřešeno",re.I)
for f in sorted(glob.glob("/home/user/tvrz-claude/docs/rozpracovane/*chyby*.md")):
    hl=None
    for n,ln in enumerate(open(f,encoding="utf-8"),1):
        if not ln.startswith("|"): hl=None if not ln.strip() else hl; continue
        b=[c.strip() for c in ln.strip().strip("|").split("|")]
        if hl is None: hl=[c.lower() for c in b]; continue
        if set("".join(b))<=set("-: "): continue
        ist=next((i for i,c in enumerate(hl) if c.startswith("stav")),None)
        st=b[ist] if ist is not None and ist<len(b) else "(bez sloupce Stav)"
        if not HOT.search(st):
            print("%s:%d #%s | %s || STAV: %s"%(os.path.basename(f),n,b[0],b[1][:150],st[:160]))
