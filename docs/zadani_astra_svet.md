ZADÁNÍ PRO STAVITELE – REALISTICKÝ SVĚT ODKAZU HAVRANA
Podklad: 60 referenčních snímků KCD1 od Míši.

ROZSAH A CÍL
Provést úpravy v celém současném světě, ne pouze na
zkušebním úseku. Zachovat rozmístění lokalit, průchodnost,
interakce a dobové prostředí českého léta roku 1393.
Reference slouží pro principy vzhledu, ne kopírování assetů.
Pracovat ve vlastní větvi. Vydat až po kontrole a testech.

Hlavní cíl: prostředí musí působit jako souvislá krajina,
ne jako jednotlivé modely rozmístěné na texturované ploše.
Optimalizace má zachovat hustotu, objem, barvu a siluety.

1. SPOLEČNÁ PRAVIDLA PRO CELÝ SVĚT
– Nejprve zmapovat všechny cesty tvorby světa: původní
  krajinu, importované díly, vegetaci a vybavení.
– Připojit je na společná pravidla materiálů, LOD, stínů,
  kolizí a vzdáleností. Nové díly nesmějí pravidla obcházet.
– Využít existující tabulku tříd; nevytvářet druhý systém.
– Změny rozdělit do přehledných commitů podle oblastí práce,
  ale aplikovat je na celý svět.
– Zachovat poslední schválený vzhled jako referenci.
– Nezkracovat plošně dohled a neředit vegetaci jako výchozí
  způsob řešení výkonu. Nejdřív odstranit zbytečné náklady.

2. TERÉN A ZASAZENÍ OBJEKTŮ
– Doplnit přirozené přechody mezi svahem, cestou, skálou,
  břehem, dvorem a základy staveb.
– Velký tvar tvoří geometrie: terénní zlomy, prohlubně,
  vystupující podloží, břehy a zářezy cest.
– Jemnou zrnitost, drobné kamínky a rýhy řešit materiálem.
– Kameny, kořeny a základy zapustit do povrchu; odstranit
  plovoucí objekty, mezery a ostré viditelné švy dílů.
– Nezvlnit všechno náhodně. Nerovnosti mají odpovídat
  svahu, erozi, pohybu lidí a způsobu používání místa.
– Vizuální detail nesmí automaticky zahušťovat kolizi.
  Kolize ale musí zachovat schody, břehy a průchozí povrch.

3. CESTY A DVORY
– Cesta musí působit jako součást terénu.
– Společná data určují její profil, materiál i ústup vegetace.
– Odstranit souvislé pravidelné zelené lemy a ostré pásy.
– Okraje nepravidelně rozšířit, zúžit a místy přerušit
  kamenem, kořenem, vyšlapanou hlínou nebo trsem.
– Rozlišit pěšinu, vozovou cestu, náves a dvůr.
– Koleje a vyšlapání vést podle skutečné trasy provozu.
– Kaluže jen do prohlubní; mokro doprovodit změnou barvy
  a drsnosti země. Ne náhodné lesklé skvrny.
– Zachovat průchody, nájezdy mostů a návaznost brodů.

4. LESY
– Rozlišit zarostlý okraj, mladý porost, vzrostlý les,
  světlinu, bor na skalách a vlhké údolí.
– Vzrostlý les nemusí být všude vyplněný keři.
  Jeho spodní patro tvoří také opad, nízké rostliny,
  kořeny, větve, kameny a místy odkrytá půda.
– Okraje a světliny zahušťovat nepravidelnými skupinami
  keřů a mladých stromků, ne rovnoměrným rozsevem.
– Střídat průhledy a zakrytá místa; zachovat možnost
  pohybu mimo cestu, kde to terén dovoluje.
– Pěšiny místy vést pod korunami, místy otevřít světlu.
– Mladé stromky řešit vhodným levným modelem.
  Pouhé zmenšení dospělého stromu nesnižuje jeho geometrii.
– Nezakrývat drahé plné stromy dalšími vrstvami listí
  v domnění, že tím automaticky klesne cena vykreslování.

5. LOUKY A PODROST
– Vytvářet propojené plochy nízké vegetace, vyšších trav,
  suchých částí a skupin květin.
– Vyhnout se stejné výšce, rozestupům a barevnosti všude.
– Květiny mají tvořit lokální skupiny, ne rovnoměrný posyp.
– Terén pod vegetací barevně sladit s jejím základem.
– „Žádná holá plocha“ znamená žádné nedodělané prázdno.
  Vyšlapaná hlína, opad nebo skalní povrch jsou legitimní.
– Podrost za hranicí detailního dosahu nesmí odhalit
  náhle prázdnou zem: použít levnější navazující podobu.
– Zachovat ekologické rozdíly suchého vršku a vlhkého dna.

6. SKÁLY, POTOKY A RYBNÍK
– Skály skládat jako navazující masivy s menšími úlomky
  u paty, ne jako stejně velké izolované balvany.
– Orientaci vrstev a barevnost sjednotit v rámci lokality.
– Mech a vegetaci soustředit do vhodných spár a míst;
  nepokrývat vše stejnou zelenou vrstvou.
– Břeh členit na vodu, vlhkou zem a sušší vegetaci.
– Rákos a lekníny rozmístit ve skupinách s volnou vodou.
– Hlídat usazení kamenů a rostlin na skutečné výšce břehu.
– Voda nemá všude působit jako čisté zrcadlo.
  Dodržet současný zákaz hint_screen_texture.

7. STAVBY A MATERIÁLY
– Sjednotit skutečné měřítko kamenů, prken, šindelů
  a došků napříč všemi modely.
– Dřevo: správný směr vláken, mírně rozdílné odstíny,
  nepravidelné konce a střídmé opotřebení.
– Zdivo: objem hlavně na rozích, ostění a velkých
  výstupcích; drobné spáry a povrch přes materiál.
– Došky: skutečná tloušťka, vrstvené pásy a nepravidelný
  okraj. Ne hladká deska s fotografií slámy.
– Šindele: čitelné řady, hrany a přiměřená nepravidelnost.
– Odstranit nápadné opakování textur pomocí variant,
  vhodného UV rozložení a velkých nenápadných změn barvy.
– Zkontrolovat normálové mapy ve formátu pro Godot,
  UV švy, měřítko a přehnanou sílu nerovností.
– Drsnost odlišit podle materiálu a vlhkosti.
  Suché dřevo a kámen nesmějí vypadat jako lakované.
– AO používat střídmě pro pevné spoje a dutiny;
  nezapékat směrový sluneční stín do základní barvy.
– Detail textur přidělit podle viditelnosti při hraní,
  nezvyšovat plošně rozlišení všech assetů.

8. VYBAVENÍ A STOPY ŽIVOTA
– Vybavovat podle účelu prostoru:
  dřevo u skladování a štípání, nádoby u práce,
  krmení u zvířat, nářadí poblíž použití.
– Zachovat volné vstupy a pracovní průchody.
– U stěn a plotů nechat nepravidelnou vegetaci,
  v používaných trasách vyšlapaný povrch.
– Přidávat funkční skupiny, ne náhodný nepořádek.
– Neinteraktivní zásoby dřeva a podobné skupiny mohou
  mít společný model a jednoduchou kolizi.
– Interaktivní předměty ponechat samostatné.
– Nepřidávat nové postavy ani herní systémy v tomto kroku.

9. SVĚTLO A VZDÁLENÁ KRAJINA
– Sladit slunce, okolní světlo, stíny a atmosféru.
– Zachovat rozdíl mezi otevřenou loukou, lesem,
  přístřeškem a interiérem.
– Ve stínu musí být čitelné materiály; ne plošná čerň.
– V dálce postupně snižovat kontrast atmosférou,
  ale nemlžit blízké okolí kvůli chybějícím objektům.
– Zachovat významné siluety skal, lesa a staveb.
– Nezavádět drahá nová světla jako náhradu za špatně
  nastavené materiály a základní osvětlení.

10. LOD A VÝKON BEZ ZTRÁTY CHARAKTERU
– Prověřit skutečné přepínání současných LOD a impostorů.
– Zjednodušovat i materiály a počet povrchů, nejen geometrii.
– Pro vzdálené skupiny použít společné levnější modely,
  pokud zachovají vzhled z různých směrů.
– Podrost musí mít navazující vzdálenou podobu.
– Velikost MultiMesh skupin volit podle měření:
  velká skupina snižuje počet volání, ale hůře se odřezává.
– Hlídání překryvů listí je stejně důležité jako počet
  trojúhelníků. Alpha scissor zachovat.
– Prolínání visibility_range v Compatibility nepovažovat
  za funkční jen proto, že je nastavené v kódu.
– Skrytou geometrii odřezávat bez děr ve viditelném světě.
  Výhledy okny a dveřmi musí zůstat úplné.
– Zachovat Compatibility, zákaz MSAA a paměťový limit
  projektu. Haldu a PSS uvádět odděleně, nezaměňovat je.

11. KONTROLA CELÉHO SVĚTA A VYDÁNÍ
– Zkontrolovat tvrz, ves, hostinec, lesy, louky, skály,
  lom, rybník a propojující cesty.
– Referenční pohledy nejsou omezením rozsahu práce:
  slouží pouze ke kontrole globálně provedených změn.
– Kontrolovat ze skutečné výšky hráče i při pohybu.
– Hledat plovoucí objekty, švy, opakování, mizení porostu,
  přeskoky LOD, kolizní vady a zakryté průchody.
– Výkon porovnávat při stejném světle, rozlišení,
  nastavení a režimu diagnostiky.
– Sledovat čas snímku, špičky a paměť; samotné snížení
  počtu kreslicích volání není důkaz zrychlení.
– Do docs/stav.md zapsat: co je nasazené globálně,
  co zůstalo výjimkou a co bylo skutečně otestováno.
– PC kontrolu nevydávat za potvrzení výkonu na tabletu.
– Do main až po kontrole. Konečné zadání a případné
  změny priorit sjednotí rádce v docs/radce.md.

HOTOVO ZNAMENÁ:
Celý svět používá společná pravidla, povrchy a objekty
na sebe přirozeně navazují, vzdálenost nevytváří holé pásy
a herní průchodnost i existující interakce zůstávají funkční.
Vzhled je doložen snímky, výkon měřením, ne pouze tvrzením.

ZPŮSOB PROVEDENÍ – ZÁVAZNÝ DOPLNĚK

Předchozí soupis je cílový vzhled celého světa.
Není to seznam volitelných námětů.

1. NEJDŘÍV PŘEČTI SKUTEČNOU IMPLEMENTACI
Projdi tvorbu terénu, cest, vegetace, importovaných dílů,
materiálů, LOD, kolizí a řízení viditelnosti.
Nevycházej pouze z komentářů nebo starých hlášení.

2. VYTVOŘ MAPU ZÁSAHŮ
Do docs/stav.md zapiš pro každý bod:
– současný mechanismus a příslušné soubory/funkce;
– konkrétní nedostatek;
– zamýšlenou změnu;
– které lokality a třídy objektů změna ovlivní;
– způsob ověření.
Potom pokračuj realizací bez čekání na další pokyn,
pokud nenarazíš na skutečný rozpor se zadáním.

3. UPRAVUJ EXISTUJÍCÍ SYSTÉMY
Nevytvářej druhý paralelní rozsev vegetace, druhou sadu
pravidel vzdáleností ani překrývající se terén.
Společná pravidla musí používat i importované díly.
Výjimky eviduj výslovně, neschovávej je v kódu.

4. ROZSAH JE CELÝ SVĚT
Neomezuj výsledek na ukázkovou scénu.
Implementuj změny postupně po systémech, ale každý
dokončený systém aplikuj na všechny odpovídající lokality.
Globální změny nemusí znamenat jeden obří commit.

5. PŘEKLAD VÝTVARNÝCH POŽADAVKŮ DO IMPLEMENTACE

„Hustý les“:
Zachovat v pohledu hráče souvislost porostu a nepravidelné
průhledy. Vzdálený detail nahrazovat levnější podobou.
Nepřidávat pouze další listí před stále plné modely.

„Přirozená cesta“:
Profil terénu, směs materiálů a vyloučení vegetace
odvozovat ze společných dat cesty.
Žádné mezery mezi nezávisle vytvořenými vrstvami.

„Realistický materiál“:
Ověřit měřítko vzoru, UV, normály, drsnost a návaznost
na okolní objekty. Pouhá výměna za větší texturu nestačí.

„Detailní objekt“:
Geometrií zachovat siluetu a velké výstupky.
Jemné povrchové detaily řešit materiálem.
Vytvořit odpovídající vzdálenou podobu a jednoduchou,
ale tvarově vhodnou kolizi.

„Optimalizace“:
Prokázat úsporu času snímku nebo paměti.
Pokles počtu trojúhelníků či draw calls sám nestačí.
Nepovažovat viditelné ochuzení za automaticky přijatelný
výsledek optimalizace.

6. NEDĚLEJ NEOVĚŘENÉ ZÁVĚRY
Screenshot KCD ukazuje požadovaný vzhled, nikoli důkaz
jejich shaderu, počtu polygonů nebo způsobu cullingu.
Uváděj zvlášť: pozorování, návrh, implementaci a měření.

7. PODMÍNKY DOKONČENÍ
U každého bodu rozliš:
– implementováno;
– zkontrolováno v renderu;
– otestováno na tabletu.
Chybějící tabletové měření označ jako neověřené.
Neoznačuj celý bod za hotový pouze proto, že kód prošel.

Zachovat interakce, průchodnost a schválený charakter
světa. Při konfliktu krásy a výkonu popsat konkrétní
varianty a jejich dopad, ne tiše plošně ubrat obsah.
