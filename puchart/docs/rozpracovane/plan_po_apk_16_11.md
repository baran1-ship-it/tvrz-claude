# Plán po APK (Míša 16. 11.)

„Postav potom APK, já projdu hru, odladíme chyby a uděláme trochu života ve světě, lovná zvěř a trofeje z ní, takže bych pak rozjel
i možnost hry, ne jen pískoviště, ale i příběh – ten by ze začátku byl jen lov, aby bylo co jíst, pečení, uzení, vaření, sušení masa
a pití vody nebo vína či piva, aby postava přežila.“

1. Míša projde APK → opravy chyb (chyby.md + testy).
1b. **PRVNÍ po APK (Míša 16. 11.): plnější příroda a scény s houštinami jako teď dělá Havran** – nejdřív zásoba MultiMeshů
   (bez záseků), časované prolnutí stromů, pak hustší podrost/houštiny/keře podle Havrana (zjistit jeho aktuální práci na
   větvi claude/new-session-0dtk58), měřit trasou na tabletu. Život (zvěř) až potom.
   **17. 11.:** zásoba MultiMeshů, časované prolnutí a houštiny hotové (chyby.md 362–365, vykon_z_havrana_15_11.md „Stav 17. 11.“,
   snímky docs/screens/priroda_*_17_11.png); čeká na schválení snímků a měření tabletu.
2. Život ve světě: zvuky prostředí (Havran ruchy.gd), zvěř – realistické CC0/CC-BY modely s kostrou, náhledy Míše na výběr,
   modelář dodělá (docs/rozpracovane/havran_prevzeti_16_11.md); chování z Havrana zvirata.gd (stanoviště v lese, útěk, spánek).
3. Lov a trofeje: luk/toulec (katalog Havrana), zásah, smrt zvěře (klip Death), vyvržení → maso, kůže, trofej (jelení trofej,
   kančí kýta… z katalogu Havrana).
4. Režim Příběh (vedle Pískoviště): začátek = přežití – potřeby hráče hlad a žízeň (ani Havran je nemá – navrhnout data
   pravidla/svet/potreby.json se zdrojem), jídlo: pečení (ohniště/pec), uzení (dýmník/udírna), vaření (kotel), sušení masa;
   pití: voda (studánka „Napít se“ už volá hrac.uhas_zizen(), studna), víno, pivo (krčma). Kazení jídla podle KCD.
Předlohy: KCD1/KCD2 (alchymie/vaření, potřeby, lov), Havran katalog předmětů.
