# Zadání 3D modelů pro hru „Odkaz Havrana“

Hra: Godot 4.4, Android tablet (Xiaomi Pad 8), Čechy roku 1393, venkovská tvrz a vesnice.
Styl: co nejvěrnější realita, podobně jako Kingdom Come: Deliverance 2. Žádný komiks, žádná fantasy.
Všechno má být opotřebované, nepravidelné a ručně dělané: ohlazené hrany, odřené dřevo, špína,
mech a lišejník, flekatá omítka. Nic nemá být dokonale rovné ani čisté.

---

## 1. Obecná pravidla (platí pro všechno)

| Co | Jak |
|---|---|
| Formát | `.glb` (glTF 2.0 binary), **jeden předmět = jeden soubor** |
| Měřítko | skutečná velikost v **metrech** (1 jednotka = 1 m) |
| Osa nahoru | **Y nahoru** (výchozí export z Blenderu „+Y Up“) |
| Počátek (pivot) | **dole uprostřed** podstavy; u věcí na zeď uprostřed **zadní** strany |
| Natočení | přední strana míří k **+Z** |
| Transformace | aplikované (Apply All Transforms), měřítko 1,1,1, žádná rotace na objektu |
| Polygony | běžný předmět **do ~40 tisíc trojúhelníků**, drobnosti (miska, lžíce) do 5 tisíc |
| Textury | jen **obrázkové** PNG nebo JPG, zabalené uvnitř `.glb`, **max 2048 px** (drobnosti 1024 px) |
| Mapy | Base Color (barva), Normal (OpenGL, Y+), Roughness (drsnost); volitelně AO a Metallic |
| Materiály | Principled BSDF napojený přímo na obrázky. **Žádné procedurální uzly** (Noise, Voronoi, Musgrave…). Před exportem je zapéct do textur. |
| Materiálů na model | co nejméně, ideálně 1–2 |
| Animace a rigging | nedělat, hra si pohyb řeší sama |
| Kamera a světla | v souboru nebudou |
| Jméno souboru | česky, malá písmena, bez diakritiky a mezer: `stul_selsky.glb`, `sud_maly.glb` |
| Varianty | `_1`, `_2`, `_3`: `kamen_1.glb`, `kamen_2.glb` |

### Ke každému modelu napiš jeden řádek popisu

```
soubor | český název | kategorie | akce | rozměr (š × v × h v m) | poznámka
sud_maly.glb | Malý sud | uvnitr | otevřít | 0.45 × 0.6 × 0.45 | dubové dřevo, železné obruče
```

**Kategorie:** `venku`, `uvnitr`, `dekorace`, `remeslo`, `zbrojnice`, `jidlo`, `skaly`, `rostliny`.

**Akce:** jakékoli z těchto: `sebrat` (do brašny), `sednout`, `lehnout`, `otevřít`, `pověsit na zeď`,
`položit na stůl`, nebo `nic`.

Jestli má předmět víko nebo dvířka, která se mají otvírat, dej je jako **samostatný objekt**
s pivotem v ose pantu a pojmenuj ho `vika` nebo `dvirka`.

---

## 2. Předměty (nábytek, nádobí, nářadí…)

- Dobové tvary pro Čechy kolem roku 1400. Žádné šroubky, hřebíky s kulatou hlavou ani soustružené
  tvary z 19. století.
- Dřevo: viditelná léta, odřené hrany a tmavší špína tam, kam sahají ruce.
- Železo: kované, nerovné, zčernalé, místy rez.
- Látky a pytle: hrubé plátno a režná pytlovina, s vráskami.
- Spodek předmětu má ležet rovně na Y = 0, ať se neboří do podlahy ani nevznáší.

---

## 3. Skály, balvany a kameny

Vzor: pískovcové skály Českého ráje (Apolena pod Troskami, Prachovské skály), žula a rula
z polí a lesů, zarostlé mechem.

| Typ | Velikost | Trojúhelníky | Variant |
|---|---|---|---|
| Kamínky na zem | 0,1–0,4 m | do 2 tisíc | 5 a víc |
| Kameny a balvany | 0,5–2 m | 5–15 tisíc | 5 a víc |
| Velké balvany | 2–5 m | 15–30 tisíc | 3–4 |
| Pískovcové věže a bloky | 5–25 m | 30–60 tisíc | 3–4 |
| Skalní stěny a výchozy (kus svahu) | 5–15 m široké | 30–60 tisíc | 3 |

**Požadavky:**
- Vypadat jako **sken skutečné skály**: lámané plochy, vrstvy pískovce, praskliny,
  zvětralé a zaoblené hrany. Žádné hladké „bramboroidy“ ani přehnaně ostré krystaly.
- **Mech a lišejník v textuře**, víc na vrchních a severních plochách, dole tmavší vlhko a hlína.
- **Spodek plochý**, pivot dole uprostřed. Ve hře se kámen trochu zaboří do země, takže
  spodních ~10 % může být hrubších.
- Textura **nesmí opakovat stejný vzor dokola** (dlaždicový efekt). Ideálně unikátní UV,
  tedy jedna textura pro celý kámen, ne opakovaná dlaždice.
- Normal mapa je důležitá, na ní stojí celá struktura. Přidej i AO, když to jde.
- Pojmenování: `skala_piskovec_vez_1.glb`, `balvan_zula_2.glb`, `kamen_maly_3.glb`, `skalni_stena_1.glb`.

---

## 4. Rostliny: keře, trávy, kapradí, stromy

**Druhy, které chci (česká krajina):**
- **Keře:** líska, černý bez, trnka, hloh, šípek, jalovec, krušina, vrba jíva, ostružiník, malinčí.
- **Byliny a trávy:** trsy trávy (vysoké i nízké), kapradí, kopřivy, lopuch, pelyněk, šťovík,
  květy (kopretina, zvonek, chrpa, vlčí mák).
- **Stromy:** dub, lípa, buk, bříza, smrk, borovice, olše, vrba (u vody), jabloň a hrušeň (sady).
- **Na zem:** pařezy, padlé kmeny, větve, hromádky listí, mech na kamenech.

| Typ | Trojúhelníky | Variant na druh |
|---|---|---|
| Trs trávy nebo bylina | 300–2 000 | 3–5 |
| Keř | 3–15 tisíc | 3–5 |
| Strom | 15–30 tisíc | 3 (mladý, střední, starý) |
| Pařez nebo padlý kmen | 2–8 tisíc | 3 |

**Požadavky (důležité kvůli výkonu na tabletu):**
- **Listí jako karty** (plošky s texturou listů a průhledností). Průhlednost dělej jako **ořez
  (Alpha Clip)**, **ne** jako prolínání (Alpha Blend).
- Listové karty oboustranné: vypni „Backface Culling“, ať jsou vidět z obou stran.
- Textura listů ve formátu PNG s průhledností (alfa kanál), max 2048 px, víc druhů listů
  klidně na jednom atlasu.
- **Kmen a větve jako skutečná 3D geometrie** s texturou kůry (barva + normal). Zblízka musí
  být kůra vidět.
- Pivot u **paty kmene** (u keře uprostřed u země), kmen kousek pod Y = 0, aby se dal zapíchnout do svahu.
- Barvy: přirozené, mírně tlumené, letní a podzimní zelená, žádná jedovatě sytá.
- Tvary nepravidelné, asymetrické, s mezerami v koruně. Žádné koule.
- **Volitelně a hodně vítané:** zjednodušená verze pro dálku (LOD) jako samostatný soubor
  `dub_1_daleko.glb`. U stromu stačí 1–3 tisíce trojúhelníků, u keře pár set.
- Pojmenování: `liska_1.glb`, `bez_cerny_2.glb`, `trava_vysoka_3.glb`, `dub_stary.glb`, `parez_1.glb`.

---

## 5. Kontrola před odesláním

1. Otevři `.glb` v prohlížeči (např. https://gltf-viewer.donmccurdy.com/) a zkontroluj,
   že jsou textury vidět a nic není růžové ani černé.
2. Rozměr odpovídá skutečnosti v metrech.
3. Model stojí na zemi (Y = 0) a pivot je dole uprostřed.
4. Normály míří ven, žádné díry ani dvojité plochy.
5. Velikost souboru do ~30 MB.

## 6. Kam to dát

- Buď poslat soubory přímo do chatu se hrou,
- nebo nahrát na GitHub do repozitáře **baran1-ship-it/tvrz-claude**, do složky **`modely/nove/`**,
  s textovým souborem `seznam.txt` (popisné řádky podle bodu 1).

Licence: vlastní tvorba, nebo zdroj CC0. U cizích modelů nebo textur napiš do `seznam.txt` odkud jsou.
