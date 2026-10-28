# Větrný mlýn – Odkaz Havrana (Čechy 1393)

**Sloupový (beraní) větrný mlýn.** Ve středověku to byl jediný typ větrného mlýna v Čechách:
celá dřevěná skříň s křídly se otáčí na jednom mohutném sloupu proti větru.

## Historie (pro rozhodnutí, kam ho dát)
- První větrný mlýn v Čechách je doložen roku **1277 na Strahově** v Praze.
- Ve 14. století byly větrné mlýny v Čechách **vzácné**. Mnohem běžnější byly vodní.
  Většina z asi 1 000 známých míst větrných mlýnů (700 z nich na Moravě) je až z pozdějších staletí.
- Kraj hry (Posázaví, Český ráj) je bohatý na vodu, takže větrný mlýn tam dává smysl jen tam,
  kde voda chybí: na **návrší nebo planině** bez potoka, například nad lomem nebo na skalní plošině.
  Jako vzácnost by ve hře mohl být zajímavý, ale nemá stát u potoka vedle vodního mlýna.

## Konstrukce
- **Kozlík** (pevný):
  - dvě křížem položené dubové ližiny (5,5 m) na čtyřech kamenných patkách, čtyři šikmé vzpěry
  - osmiboký sloup se železnou obručí, vysoký 4,7 m
  - vše je z tmavého starého dubu s mechem
- **Skříň** (otočná), 3,4 × 4,4 m, dvě patra, sedlová střecha:
  - nese ji hlavní trám (sedlo), který leží na vrcholu sloupu
  - rám z trámů obitý vodorovnými prkny přes sebe, střecha z prken ve dvou vrstvách
  - *dolní patro:* sloup prochází podlahou, moučnice s moučným žlabem, pytle, žebřík nahoru
  - *horní patro:* kameny v lubu, násypka s obilím a cevník, do kterého zabírá palečné kolo se 48 palci
- **Vzadu** jsou schody ke dveřím a vedle nich **oj**, dlouhý trám, kterým mlynář natáčí celou skříň proti větru.
- **Křídla**: čtyři mřížová křídla o průměru 10,8 m na dvou ramenech protažených křížovou hlavou.
  Plátno je mírně vyduté, přivázané k ramenu a k okrajové lati. Hřídel je osmiboká, se sklonem 8°.

## Funkce ve hře (hierarchie uzlů)
```
Vetrak_Kozlik                 – pevný (kolize: patky, ližiny, sloup)
Vetrak_Skrin                  – otáčí se kolem svislé osy (Y v Godotu) proti větru
 ├─ Vetrak_Kridla             – otáčí se kolem své lokální osy +Z (v Godotu) = osa hřídele
 ├─ Vetrak_Dvere              – počátek v pantu, otevírá se o ~100°
 └─ Vetrak_Kol_*              – kolize skříně (podlahy s otvory, stěny s dveřmi, schody, žebřík, lub…)
```
- Křídla: v `_process` stačí `kridla.rotate_object_local(Vector3(0, 0, 1), rychlost * delta)`
  (asi 1,5–2 rad/s). Palečné kolo uvnitř je součástí křídel a točí se s nimi.
- Natočení proti větru: `skrin.rotation.y = smer_vetru`. Kolize skříně jsou její potomci a otočí se s ní.
  Pokud se má skříň za hry otáčet i fyzicky, použijte místo StaticBody AnimatableBody3D.
- Spodní konec křídla je 2,3 m nad zemí, takže pod ním hráč projde, ale je to těsné.
  Případně tam dejte kolizní oblast, ať hráče točící se křídla shodí.
- Do horního patra se leze vnitřním žebříkem otvorem v podlaze. Lezení je potřeba ve hře udělat jako interakci.

## Výkon
≈ 44 700 trojúhelníků (otesané trámy, kolíky, pásy s nýty, kování).

Generátor: `vetrak.py`. Spuštění: `python vetrak.py --norender`.
