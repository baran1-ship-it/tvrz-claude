# Stav 16. 11. večer (limit session do 22:09) – vydání 0.9999991
Hotovo: export_vse OK (974 s), dlaždice OK, moje testy OK kromě ryb_vznaseni (známý zbytek 6 vrcholů, ř. 6 tabulky).
Agenti hotovi: sady 1400 (zprávy v misa_16_11_sady.md), scény (sceny_kcd_15_11.md).
Běží: export_vse2 (kvůli clona vjezd_houstina_sv 7 m, commit 5e8e43c).
Po exportu:
1. testy clona_vsi, houstina_volno, zasazeni, postele_domu, ohen_u_pece (TVRZ_TEST_LIMIT=1500, skupina).
2. OTEVŘENÉ ve snímcích (prohlédnuto mnou): dum1.png pec černá + stín přes jizbu (Dum1 a Dum2 pec yaw 90, Rychta yaw 0
   vypadá dobře; podezření světlo ohně se stíny uvnitř kopule / orientace ústí – NEOVĚŘENO); zemljanka3 deka jasně modrá,
   houně šedomodrá (podezření ambient interiéru); náves světle zelené čáry na hlíně (hrana masky, bylo i dřív);
   řady trsů louky ve vsi (podezření louka.gd). Rychta: pec uprostřed jizby, ne v rohu.
3. nezávislá kontrola subagentem, celá sada, otisk_exportu.py over, vydani.py 0.9999991 --testovaci --jen z_svet,z_krcma,
   z_kostel,z_ruiny_ves,z_ves,z_rostliny,z_katalog,z_reka,tex_predmety2,z_dlazdice + 41 p_* (bez z_postavy).
