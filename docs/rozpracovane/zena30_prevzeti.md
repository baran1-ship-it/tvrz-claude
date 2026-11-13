# Převzetí postupu zena30 (Míša 13. 11., skripty od modeláře v tools/zena30/)

Stav: uloženo jako podklad, NEZAPOJENO. Cíl na další verzi: postup pro všech 32 NPC, ne jedna postava.

## Co převzít
- `rig_sim.py`: 24 řetězů × 4 kosti (`chain_weights` podle úhlu a výšky), simulace zapečená do rotací kostí v každé
  animaci (náběh z klidu, tuhost tvaru, vyhlazení po obvodu, omezení obvodu, kolize bodů i úseček s kapslemi,
  směr ven od těla / u vodorovné kapsle nahoru, max. posun za krok). Za běhu nic → `scripts/sukne_ridic.gd` odpadne.
- `fit_caps.py`: kapsle z řezů těla (u nás dnes ruční poloměry v `pravidla/svet/postavy.json` sukne).
- `outfit.py`: tělo pod oblečením vyříznuté (u nás jen zasunuté `pod_vrstvou`).
- `clip_test.py`: test prořezu na síti v Blenderu přes všechny klipy (doplní `tools/test_sukne.gd`).

## Co upravit
- Pevné cesty `/home/claude/...` (common.py, anim_util.py, začátek rig_sim.py a fit_caps.py) → naše `tools/postavy_q`.
- Klipy: zapéct do NAŠICH knihoven (`modely/postavy/anim/UAL_prace.glb` aj., 48 klipů činností), ne jen UAL1/2.
- Nejvýš 4 váhy na vrchol už v Blenderu před zapečením (jinak sukne × zástěra jinak než v testu).
- Rozpočet: NPC LOD0 ≤ 14 000 troj., jeden mesh + atlas (q_export2.py) – zena30 má 26 500 a 11 dílů / 8 materiálů.
- Čísla z `params.json` do `pravidla/svet/postavy.json` (žádná čísla v kódu).
- Cena: zapečené kosti sukně (96) zvětší knihovny animací – změřit velikost .glb a paměť na tabletu.
