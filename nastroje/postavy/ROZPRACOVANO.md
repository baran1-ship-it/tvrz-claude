# Postavy – rozpracováno (pozastaveno 15. 10. kvůli skalním věžím)
- Základ těl: MPFB2 (CC0), Blender extension (mpfb_boot.py), kostra game_engine (UE názvy kostí).
- char_build.py <jmeno> <pohlavi> <vek> [svaly] [vaha] [vyska] -> <jmeno>_base.blend; tvar obličeje z faces.json
- head_build.py <muz|kluk>: kůže (skin_mat.py), obočí, strniště, vlasy jako slupka (head_features.hair_shell), barva očí (eye_recolor.py)
- outfit.py <muz|kluk> <kroj>: oblečení ze slupek těla a trubek ze řezů (clothes.py), materiály cloth_mat.py; váhy z těla -> hýbe se s kostrou
- char_render.py: náhled (POSE=1 spustí ruce dolů)
- Fit obličeje na fotku: lmk.py (dlib 68 bodů, modely z pip balíku face_recognition_models), fit_prep.py (render + body + delty targetů), fit_solve.py (least squares)
- Stav: vlasy OK, kůže zatím figurína (čeká se na CC0 skin textury od Míši nebo projekci fotky), oblečení v1 – sukně kabátce chytala ruce (opraveno), pláštík moc široký.
- Další krok: fit obličeje muže na fotky (přední + profil), projekce fotky do textury, kluk výška 13 let ~1,55 m (vyska ~0.35), oblečení kluka, zapečení textur, export glb.
- Kluk: vždy jen oblečený.
