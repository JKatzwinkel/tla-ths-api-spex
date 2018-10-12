# tla-ths-api-spex

wie man thesauruseintraege des berliner altaegyptischen woerterbuches abrufen und suchen soll


## struktur einer response & error signaling

Jede antwort hat eine kanonische form, die immer einen vollständigen `header` und ein 
`result`-feld mit inhalt gemäß dem endpoint enthält. die (plain text) `description` im 
header dient der anzeige für die user und ist bei einem status `error` obligatorisch.

```json
{
  "header": {
    "status": "success|error",
    "code": …,
    "description": "could not find entry with ID TL3NBDJXXZE7RKWNRVQS5TPSB",
    "object_base_url": "http://tladev.bbaw.de/get/{id}"
  },
  "result":
     // endpoint-spezifisch 
}
```


## endpunkte

### `/ths/get/<string:id>`

- method: `GET`

Man gibt die **26**-stellige (:point_up:) ID des thesauruseintrags an und bekommt eine 
`application/json` response folgender art:

```json
{
  "id": "CLJN6LLO5NDL7DY6HOP4XC4ELE",
  "name": "Butler, Cuthbert",
  "type": "person"
}
```    

im falle eines fehlers steht im `result`-feld der response ein `null`. 


### `/ths/get/<string:id>/<string:relation>`

- method: `GET`

Man gibt zusaetzlich zur **26**-stelligen (:point_up:) ID noch den namen der beziehung 
an, deren objekte man haben will. Moeglich sind `roots`, `parents` und `children`. Man erhält 
eine JSON response mit einer liste (ein eintrag kann mehrere wurzelelemente haben) von URLs 
von objekten. Wie im endpoint `search` kann der parameter `type` zum filtern angegeben werden.

```json
[
  "CLJN6LLO5NDL7DY6HOP4XC4ELE",
  "NDLBDCMPELEJNC4Y66FO5S4XHO",
]
```

im falle eines fehlers steht im `result`-feld der response ein `null`.


### `/ths/search`

- method: `GET`

Man sucht eintraege deren `name` feld mit dem angegebenen `term` beginnen oder ihn 
beinhalten. Das ergebnis ist eine liste von objekten, enthalten im `results`-feld der 
`application/json`-response. Die einzelnen results enthalten jeweils `id`, `name` und 
`type`.

Folgende parameter müssen oder können angegeben werden:

|name|range|funktion|default|
|---|---|---|---|
|`term`|mindestens 2 zeichen lang|suchbegriff der im `name` vorkommen soll|**required**|
|`mode`|`{prefix\|contains}`|ob `term` am anfang von `name` oder irgendwo steht|`prefix`|
|`limit`|1-50, `int`|wie viele ergebnisse maximal|`50`|
|`offset`| |Index des ersten Items in den Gesamtergebnissen|`0`|
|`type`|liste von strings|man kriegt nur ergebnisse, deren `type` im parameter kommagetrent genannt sind|`[]`|

Die ergebnisse werden alphabetisch sortiert nach `name` und auf `limit` oder `50` stueck 
begrenzt. Beispiel:

```bash
    curl http://tladev.bbaw.de:5002/ths/search?term=ha&limit=5
```

```json 
{
  "total": 23,  // lti!
  "offset": 0,
  "objects": [
    {
      "id": "7QGME3V2XZDN3IJKDWHZJWHEWU", 
      "name": "Haags Gemeentemuseum", 
      "type": "location"
    }, 
    {
      "id": "IX35XEUNPNFBNDU4UNB4CQRTXA", 
      "name": "Haar", 
      "type": "material"
    }, 
    {
      "id": "3MMFFLHZI5F4DHBJTX2Q7PI3JA", 
      "name": "Haarkranz", 
      "type": "objecttype"
    }, 
    {
      "id": "W6EYN4YCLBEV7JGI5JVHLPKRL4", 
      "name": "Habachi, Heqaib", 
      "type": "bibliography"
    }, 
    {
      "id": "TEG7S6IMBRAUHL5JHPYTMDKL34", 
      "name": "Habachi, Kamose", 
      "type": "bibliography"
    }
  ], 
}
```


im falle eines fehlers steht im `result`-feld der response `{"total": 0, "offset": 0,"objects": []}`.

Weitere Beispiele:

```bash
curl http://tladev.bbaw.de:5002/ths/search/?term=ha&type=person,location

```
