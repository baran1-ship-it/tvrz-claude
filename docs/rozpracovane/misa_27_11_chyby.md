# Míša 27. 11. – tablet 0.9999999 (snímky `docs/screens/misa_27_11/01–19`)

Míša: „voda v potoce super ale břehy zubaté nepřirozené, nastuduj si to; za vesnicí louky jsou nějaké chudé; fps super
ale bez trávy; v lese zase kořen, který už ve hře nemá cíl; kuchařka ubrat animace, nemůže ležet v ohni ani na něj
sahat, kotlík je pro ni cíl; vlasy borec na dvoře; kůň žere s ohnutým krkem, promysli to; jízda taky nic moc oproti
původnímu, musíš to nějak sladit … animace a postavy jsou další level, takže si udělej širokou a hlubokou rešerši,
jak to řeší jiné hry, a s tím se řiď“.

| # | Co Míša viděla | Rozbor | Oprava (záznam/pravidlo) | Kontrola | Stav |
|---|---|---|---|---|---|
| 1 | Břehy potoka zubaté, nepřirozené (11, x −2 z 25 u tvrze) | | | | ROZBOR |
| 2 | Louky za vesnicí chudé (02–04, x 364–558 z 1037–1062) | | | | ROZBOR |
| 3 | FPS dobré, ale bez trávy (GPU tráva vypnutá?) | | | | ROZBOR |
| 4 | V lese kořen bez smyslu (09, x 227 z 363) | POTVRZENO (kód): kořenový talíř `root_cluster_01` sázel `svet._krajina` samostatně 1,5–3 m od padlého kmene – s ničím nesouvisel | samostatný kořen se nesází; vývrat = kmen s kořenem jako jeden záznam (zatím není) | NEOVĚŘENO snímkem | OPRAVENO v kódu |
| 5 | Kuchařka: moc animací, leží v ohni / sahá do ohně; kotlík = cíl (12–13, x −2 z −12) | | | | ROZBOR |
| 6 | Vlasy mladíka na dvoře tvrze – černé střepy (14, x −5 z 6) | | | | ROZBOR |
| 7 | Kůň se pase s krkem ohnutým dozadu do C (17, 19) | POTVRZENO izolovaným snímkem (`tools/foto_kun_pastva.gd`, `docs/screens/misa_27_11/oprava/`): pastva skriptem `kun_zivy` (krk 75° rovnoměrně po 4 kostech + hlava 18°) = oblouk, huba ke hrudi; autorský klip modelu „Eat“ = krk vpřed dolů | pastva = klip modelu ve smyčce prolnutý podle času pastvy (`jizda.json kun.zivy.pastva_klip`), skript krk neohýbá | test `kun_pastva` (hlava ≥ 0,4 m pod krkem a ≥ 0,2 m před ním; naměřeno 0,57 / 0,48) | OPRAVENO, OVĚŘENO snímkem a testem |
| 8 | Jízda horší než s původním koněm – sladit (18) | | | | ROZBOR |
| 9 | Animace a postavy: široká a hluboká rešerše jiných her | rešerše `reserse_animace_postavy_27_11.md` | | | ROZPRACOVÁNO |
