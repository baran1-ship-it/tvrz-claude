# Předloha Míši (video, znovu poslané 18. 11.): LOD stromů a tráva v dálce
- 01–10 stromy: časované prolnutí LOD (0,25 s místo pásma) – u nás už je (stromy_modely.json lod_casove, 17. 11.);
  LOD0→LOD1→LOD2→LOD3→impostor (1081/787/524/361/2 troj.) – u nás chybí LOD1–3 z Blenderu (plán A4).
- 11–14 tráva: jemné karty blízko, dál přechod ditherem (maska) do levnější vrstvy, „after“ bez viditelné hrany.
- 15–20 pole: karty jen blízko (~500 buněk), dál **impostor buňky** (2 troj. na buňku s pečenou texturou trsu
  /pole), celkem 41k troj. místo 83k a výsledek vypadá stejně → základ pro plán E1/E2 (střední pás a dálka).
