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
| Y ve stání (nápověda „Y Sesednout“ vpravo dole) | tlačítko **Sesednout** nad tlačítkem ostruhy (jen ve stání) | sesednout |
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

## Opraveno 5. 11. (Míša 0.99991)
- „Na dotykovém ovládání nevím, jak slézt z koně“: držení ostruhy ve stání nebylo objevitelné. Jako KCD2 (sesednutí má
  vlastní tlačítko Y / E s nápovědou; https://outsidergaming.com/kingdom-come-deliverance-2-controls-guide/): na koni ve
  stání se nad tlačítkem ostruhy (60 px mezera, s lukem mimo kruh napínání) ukáže pergamenové tlačítko **Sesednout** (`hud.gd _btn_sesednout`; sesedne se až při puštění prstu uvnitř tlačítka), na ovladači nápověda
  „Y Sesednout“. Svitek akcí na koni se nevrací. Při plavání sesednout nejde (`kun.stoji()`).
- Kůň brodí a plave (`jizda.json kun._voda`), zastaví jen před srázem (`sraz_m`, povrch z fyziky – mostovka je povrch).
- Rychlé cestování na koni: přesune se kůň i jezdec (`kun.premisti`, `main.fast_travel`).
