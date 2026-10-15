# Zadání zvuků pro hru „Odkaz Havrana“

Hra: Godot 4.4, Android tablet (Xiaomi Pad 8), Čechy roku 1393: venkovská tvrz, ves Lhota, zájezdní hostinec,
lesy, potok, pískovcové skalní město. Styl jako Kingdom Come: Deliverance 2: věrná realita, žádná fantasy,
žádné moderní zvuky (motory, sklo lahví, kovové zipy, moderní hudební nástroje).

Ty děláš jen zvuky a hudbu. Do kódu hry nezasahuješ, zvuky do hry zapojí druhý chat.

---

## 1. Pravidla

| Co | Jak |
|---|---|
| Zdroje | jen licence, které dovolí hru volně šířit: **CC0** (Freesound s CC0, Sonniss GDC balíky, OpenGameArt CC0, Pixabay), **CC BY** (autora uvedeme v titulcích). **Ne** CC BY-NC, ne „jen pro osobní použití“, ne nic bez licence. |
| Vlastní tvorba | povolena (syntéza, střih, vrstvení), ale musí znít jako skutečná nahrávka |
| Formát | **Ogg Vorbis** (`.ogg`), 44,1 kHz, kvalita ~5 (asi 160 kb/s) |
| Kanály | jednorázové zvuky (kroky, dveře, údery) **mono**; ruchy prostředí a hudba **stereo** |
| Hlasitost | jednorázové zvuky špička −3 dBFS; ruchy prostředí kolem −20 LUFS; hudba kolem −16 LUFS. Všechno vyrovnané, ať nic nevyčnívá. |
| Střih | žádné ticho na začátku (zvuk začne do 10 ms), konec doznívá přirozeně, žádné cvaknutí |
| Smyčky | ruchy prostředí 60–120 s, **plynulá smyčka bez švu** (crossfade konce do začátku) |
| Varianty | u opakovaných zvuků (kroky, údery, vrzání) **5–8 variant**: `_1` … `_8`, každá trochu jiná (síla, výška, délka) |
| Jména | česky, malá písmena, bez diakritiky a mezer: `krok_trava_1.ogg`, `ves_den.ogg` |
| Šum a čistota | bez šumu nahrávání, bez hlasů v pozadí, bez moderních zvuků (auta, letadla, sirény) |

### Ke každému souboru jeden řádek do `seznam.txt`
`soubor | co to je | zdroj (odkaz) | autor | licence | poznámka`

---

## 2. Co je potřeba (podle důležitosti)

### A. Kroky (nejdůležitější, dnes znějí synteticky)
Hráč chodí v kožených botách bez podpatku (středověká obuv). Pro každý povrch **8 variant chůze** a **4 varianty běhu**:
`krok_trava`, `krok_hlina` (udusaná cesta), `krok_blato`, `krok_sterk`, `krok_kamen` (dlažba, kamenná podlaha),
`krok_drevo` (prkenná podlaha), `krok_most` (dutá prkna mostu), `krok_listi` (les), `krok_voda` (mělká voda), `krok_seno`.
Doskok po skoku: `doskok_<povrch>` 3 varianty.

### B. Ruchy prostředí (smyčky)
- `les_den`, `les_noc` (sova, cvrčci, praskání větví)
- `louka_den`, `louka_noc`
- `ves_den` (slepice, husy, kráva v dálce, pes, kovář v dálce, děti), `ves_noc`
- `tvrz_nadvori` (kroky stráže v dálce, kůň, vítr ve štítech)
- `senk` (hovor hostů nesrozumitelně jako hučení, cinkání korbelů, smích, praskání ohně), `senk_prazdny`
- `potok` (malý potok přes kameny), `rybnik` (žáby, kachny), `vitr_skaly` (vítr ve skalách)
- `dest` (venku), `dest_strecha` (déšť na šindelové střeše zevnitř), `bourka_hrom` (5 variant hromu zvlášť)
- `krb` (praskání ohně, smyčka), `pec_kovarna` (měch a výheň)

### C. Předměty a činnosti
- dveře: `dvere_otevrit`, `dvere_zavrit`, `vrzani` (5 var.), `zapadka`, `zavora` (dřevěná závora)
- truhla a skříň: `truhla_otevrit`, `truhla_zavrit`, `skrin_otevrit`, `skrin_zavrit`
- zvedání a pokládání podle materiálu: `polozit_drevo`, `polozit_kov`, `polozit_keramika`, `polozit_latka` (každé 4 var.)
- `mince` (4), `mesec`, `listovat` (kniha), `korbel_napit`, `jist` (kousnutí chleba), `nalit_pivo`
- louč a svíce: `louc_zapalit`, `louc_hori` (smyčka), `louc_zhasnout`, `svice_sfouknout`
- kovárna: `kovadlina` (8), `kaleni` (syčení), `mech`
- luk: `luk_napnout`, `luk_vystrel`, `sip_zasah_drevo` (4), `sip_zasah_terc` (4), `sip_zasah_zem` (4)
- studna: `rumpal` (smyčka), `vedro_do_vody`, `vedro_voda`
- padací most a mříž: `retez` (smyčka), `rohatka`, `dopad_most`, `dopad_mriz`
- `sednout` (dřevěná lavice zavrže), `lehnout` (slamník), `spanek` (přechod: krátké ticho, ranní ptáci)

### D. Zvířata (jednotlivě, 3–5 variant)
`kohout`, `slepice`, `husa`, `krava`, `kun_rehtani`, `kun_odfrknuti`, `pes_stekot`, `ovce`, `prase`, `vrana`, `sova`, `datel`, `kukacka`, `zaba`

### E. Rozhraní (střídmě, dobově)
`menu_otevrit` (šustnutí pergamenu), `menu_vyber` (tiché ťuknutí do dřeva), `menu_zpet`, `ulozeno` (pečeť do vosku),
`ukol_novy` (krátký motiv na loutnu nebo fidulu, 2 s)

### F. Hudba (volitelně, až po A–E)
Dobová hudba na dobové nástroje: loutna, fidula, flétna, šalmaj, dudy, bubínek, harfa, gotický chorál.
Kolem roku 1400, ne renesance ani baroko. Zatím hraje Kevin MacLeod (CC BY 4.0). Náhrada je vítaná, pokud bude dobovější.
`menu`, `tvrz_1`–`3`, `ves_1`–`3`, `krajina_1`–`3`, `senk_1`–`3` (živá hudba v hostinci), `noc_1`–`2`. Každá 2–4 minuty, smyčka.

---

## 3. Odevzdání

- Ukládej do repozitáře **baran1-ship-it/tvrz-claude**, větev **main**, složka `zvuky/nove/`, podsložky podle oddílů:
  `kroky/`, `prostredi/`, `predmety/`, `zvirata/`, `rozhrani/`, `hudba/`.
- Do `zvuky/nove/seznam.txt` zapiš každý soubor (zdroj, autor, licence).
- Velké soubory (hudba nad 20 MB) ne do gitu, napiš je zvlášť a domluvíme se.
- Odevzdávej po oddílech (nejdřív A kroky), ať je můžu průběžně zapojovat a zkoušet na tabletu.
- Neměň nic mimo `zvuky/nove/`.
