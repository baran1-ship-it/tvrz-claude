# Ovládání – herní ovladač (Xbox) a dotyk

Zdroj pravdy v kódu: `scripts/pad.gd` (ovladač), `scripts/hud.gd` (dotyk), `scripts/kun.gd` (jízda),
`pravidla/svet/jizda.json` `kun.ovladani_popis`, `ostruha_klepnuti_s`, `sesednout_drzet_s`.
Input Map v `project.godot` se nepoužívá – ovladač čte přímo `Input.get_joy_axis` / `InputEventJoypadButton`
(zařízení 0), mrtvá zóna pák radiální `pad.gd DEAD` 0,16.

## Pěšky
| Ovladač | Akce |
|---|---|
| levá páčka | chůze (stisk páčky = běh, do puštění) |
| pravá páčka | rozhlížení |
| A | akce ze svitku u předmětu, jinak skok |
| Y | nasednout na koně (je-li na dosah), jinak denní doba (zkouška) |
| B | konec stavění / let (jen pískoviště) |
| D-pad dolů / nahoru | svitek akcí, jinak menu hráče / mapa |
| D-pad vpravo | stavění |
| RT | napnout a pustit luk |
| Start / Back | pauza |

## Na koni (jako KCD, Míša 4. 11.)
| Ovladač | Dotyk | Akce |
|---|---|---|
| levá páčka vpřed | páčka vpřed | krok; puštění = kůň zastaví |
| levá páčka vzad | páčka vzad | couvání |
| levá páčka do stran | páčka do stran | zatáčení; pohled jezdce se točí s koněm |
| pravá páčka | tah prstem | rozhlížení (do `rozhled_st` od směru koně); kůň v chůzi zatáčí za pohledem, když páčka neřídí |
| A klepnutí (< `ostruha_klepnuti_s`) | tlačítko skoku klepnutí | ostruha: o chod rychleji (krok → cval) |
| A držení | tlačítko skoku držení | trysk (ubývá výdrž koně) |
| A držení ve stání (`sesednout_drzet_s`) | totéž | sesednout |
| Y ve stání | – | sesednout |
| B, stisk levé páčky | – | nic (na koni nespouští let ani běh) |
| D-pad dolů / nahoru, Start | – | menu hráče / mapa / pauza |

Rešerše: KCD2 na Xbox sesedá tlačítkem Y (https://dotesports.com/kingdom-come/news/all-kingdom-come-deliverance-2-controls-pc-and-console-keybinds,
https://www.magicgameworld.com/?p=108691); tlačítko pro cval/trysk koně na ovladači tam uvedené není – ponechána
ostruha na A podle zadání Míši (klepnutí / držení).

## Opraveno 4. 11. (Míša 0.9998 „špatné ovládání na Xbox ovladači“)
- Ostruha z ovladače nefungovala: `kun.gd` čte držené tlačítko z `player.fly_up`, ale `pad.gd` ho nastavoval jen v letu.
  Na ovladači proto kůň nešel do cvalu ani trysku a sesednout držením nešlo. Teď `fly_up` = držené A na koni.
- A na koni volalo `player.jump()` (dvojklepnutí na pískovišti zaplo let v sedle), Y měnilo denní dobu, B zapínalo let.
  Na koni teď A jen ostruha, Y ve stání sesedne, B a stisk páčky nic.
- Řízení páčkou do stran: pohled zůstal na místě, po puštění páčky kůň zatočil zpátky za pohledem (směr nešel udržet).
  Teď se pohled při řízení páčkou točí s koněm (`kun.gd _rizeno`).
