# Vedlejší linka: Milostivé léto

**V kostce:** V hostinci U Zlatého kola někdo v noci podřízl poutníka Šimona. Byl to otcův posel,
nesl z Prahy svitek se jmény spiklenců. Hostinského Ondřeje obvinili z vraždy a královský biřic
Vilém Sup ho chce oběsit. Skutečný vrah je „kupec“ Konrád, Kostkův žoldnéř. Svitek odnesl kněz Prokop,
který spal ve stejném pokoji a utekl do krypty zříceného kostelíka. Hledá ho Sup i Konrád.

**Odemkne se:** kapitola 2 (Anežka přiběhne na tvrz). **Hrát do:** kapitoly 4 (svitek je potřeba k volbě strany).
**Ladění:** detektivka, noc na hřbitově, strach z moci.
**Historie:** milostivé léto 1393 (poutníci do Prahy), spor krále s arcibiskupem Jenštejnem,
umučení Jana z Pomuku 20. 3. 1393. O mučení se ve hře jen mluví.

---

**M1 – Mrtvý v pokoji tři** · *hostinec, pokoje*
Anežka vede Jana nahoru. Šimon leží na posteli, hrdlo podřezané, krev na podlaze i na stěně.
Druhá postel je prázdná a rozházená. Vilém Sup a dva biřici drží Ondřeje ve sklepě.
Sup: hostinec stojí na Janově půdě, takže soudit má Jan – ale Sup dává **tři dny**, pak Ondřeje oběsí sám.
**Příznak:** `M_mrtvy`.

**M2 – Stopy** · *hostinec, kupecký stan*
Najdi důkazy (pořadí libovolné, stačí 3 ze 4):
1. **nůž** v latríně za hostincem – kupecký nůž s řezenskou značkou, ne kuchyňský,
2. **krvavé otisky bot** na schodech – hostinský chodí v dřevácích, tohle jsou jezdecké boty s ostruhou,
3. **Anežka** viděla v noci na chodbě „kupce“ v plášti, myslela, že jde na latrínu,
4. **kupecký stan:** sudy jsou plné kamení a slámy, žádný kupec. Pod polštářem měšec s 5 kopami v nových groších.
Šimonovy sandály mají **dvojité dno** – prázdné. Někdo z něj něco vytáhl, nebo to Šimon měl jinde.
**Příznak:** `M_dukazy` (počet).

**M3 – Kdo spal vedle** · *hostinec → kostelík*
Hostinský přes mříž sklepa: ve druhé posteli spal poutník-kněz Prokop, „bledej jak smrt, bál se každýho“.
Venku stopy bosých nohou v blátě vedou k lesu. U kostelíka sv. Jiljí jsou ty samé stopy, které Jan viděl na pohřbu.
**Příznak:** `M_prokop_stopa`.

**M4 – Noc na hřbitově** · *kostelík sv. Jiljí, krypta (nová), noc*
Jen v noci, s loučí. Hřbitov: vyvrácené náhrobky, otevřený hrob, sova. Ve kryptě kostnice s lebkami ve výklencích.
Prokop se brání svícnem. (ROZHOVOR) Vypráví, proč utekl z Prahy: viděl, jak královi lidé odvedli arcibiskupovy úředníky,
a slyšel, co se s nimi dělo. Šimonovu brašnu vzal, protože Šimon mu řekl: „Kdyby se mi něco stalo, dones to Havranímu.“
V brašně: **Šimonův svitek** (zapečetěný, latinsky). Dá ho Janovi, jen když slíbí, že ho ochrání.
**Příznak:** `ma_svitek`, `prokop_nalezen`.

**M5 – Psi v lese** · *les, kostelík, noc*
Té noci přijdou ke kostelíku Konrádovi muži (3, BOJ) pro svitek. Zároveň v dálce štěkají Supovi psi.
Bránit kryptu, pak rozhodnout, kam s Prokopem:
- **vydat ho Supovi:** Sup je vděčný (strana Král je pak snazší), Prokopa odvezou do Prahy. Co tam s ním bude, se nedozvíš.
- **schovat ho na tvrzi:** v podkroví věže. Když ho tam Sup najde, je zle (`sup_nepritel`).
- **převést ho přes skály:** poustevník Bartoloměj zná stezku skalním městem. Noční doprovod, vyhýbat se psům a loučím biřiců.
  Na konci Prokop odejde do kláštera za hranice panství.
**Příznak:** `prokop` = `vydan` | `ukryt` | `preveden`.

**M6 – Soud v šenku** · *hostinec*
Jan soudí v šenku před lidmi. Předloží důkazy, Konrád se směje – dokud Anežka neukáže na jeho boty s ostruhou.
Konrád vytáhne nůž (BOJ v šenku, převržené stoly). Když přežije, přizná, že ho poslal Kostka.
Ondřej je volný. Sup uzná Janův soud.
Volba s Konrádem: **oběsit** u rozcestí / **vydat Supovi** / **vyměnit** Kostkovi za otcův úpis (Kostka souhlasí, ale nedodrží to).
**Hotovo:** `leto_konec`, `ondrej_ocisten`, `konrad` = ...

**Odměny:** hostinský dává Janovi podíl ze šenku (pravidelný příjem), Anežka nosí na tvrz zprávy z cesty.
Svitek je klíčový pro **H3.5** a **H4.2**.
