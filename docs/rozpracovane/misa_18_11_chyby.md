# Míša 18. 11. – tablet 0.9999993 (snímky `docs/screens/misa_18_11/`, měřicí trasa 03:07)

Míša: „ves byla super a začala se zase sekat; scény mají být chytré, ne že se všechno nahrne na jedno místo“.

| # | Co Míša viděla | Rozbor | Oprava (záznam/pravidlo) | Kontrola | Stav |
|---|---|---|---|---|---|
| 1 | Strom ve vsi žlutý (03 x 421 z 767 zevnitř, 04 x 411 z 784 jabloň) | POTVRZENO v kódu: moje oprava 17. 11. ř. 3 v `listi_jadro.gdshader` dělila barvu nejmenšího mipu jeho alfou – na tabletu alfa skoro 0 → přepálené do žluta | odstín průměru listů normovaný na nejsilnější kanál, pevný tmavý jas 0,3; mip bez barvy → tmavě zelená | snímek jabloně 04 | OPRAVENO v shaderu – čeká na snímek a tablet |
| 2 | Tvrz: lavice pod schody (01 x 5 z 3), „měla být u zdi“ | | | | OTEVŘENO – rozbor (pomocník) |
| 3 | Lidé na tvrzi zase všichni u brány, mají být roztroušení | | | | OTEVŘENO – rozbor (pomocník) |
| 4 | Řada lidí jdoucí od tvrze po cestě (02 x 4 z 72) – co to je? | | | | OTEVŘENO – rozbor (pomocník) |
| 5 | Animace otevírání bedny v hospodě zrušit (hlavní, co tam lidé dělají) | | | | OTEVŘENO – rozbor (pomocník) |
| 6 | „Udělal jsi tam les, ale další část obce je prázdná“ – houštiny nahrnuté na jedno místo, scény mají být chytré | | | | OTEVŘENO – rozbor (pomocník) |
| 7 | Kolem míst, kde se chodí, nemá být tráva – před kovárnou trávy moc | | | | OTEVŘENO – rozbor (pomocník) |
| 8 | Kopřivy pod ploty nechtěl – jen jedna, moc; podle fotek z KCD | | | | OTEVŘENO – rozbor (pomocník) |
| 9 | Ves se zase seká (měření 03:07: ves-vjezd p95 40, „vše znovu“ 53, >40 ms 16 → 180) | měření: tvrz-cesta p50 47 → 28 (dlaždice fungují), ves-dvory 44 → 31; ves-vjezd „vše“ 30/40 vs „vše znovu“ na konci 43/53 – drift během trasy (teplo/paměť: halda 1795 MB, VRAM 1099), varianty bez postav/houštin/obzoru ve vsi bez jasného rozdílu; špičky hostinec 330 a 3250 ms, zahřátí krčma 3782 ms | | | OTEVŘENO – rozbor po opravách 1–8 (měřit znovu) |
