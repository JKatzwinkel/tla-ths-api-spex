# tla-ths-api-spex
wie man thesauruseintraege des berliner altaegyptischen woerterbuches abrufen und suchen soll

## endpunkte

### `/ths/get/<string:id>`

- method: `GET`

Man gibt die **26**-stellige (:point_up:) ID des thesauruseintrags an und bekommt eine `application/json` response folgender art:

```json
    {
      "children": [],
      "id": "CLJN6LLO5NDL7DY6HOP4XC4ELE",
      "name": "Butler, Cuthbert",
      "parents": [
        "http://.../ths/get/OJDRAHAIX5BMND7OQH3TKTG4C4"
      ],
      "type": "person"
    }
```    
    
### `/ths/get/<string:id>/<string:key>`

- method: `GET`

Man gibt zusaetzlich zur **26**-stelligen (:point_up:) ID noch den namen der eigenschaft an, die man haben will. Moeglich sind `name`, `type`, `roots`, `parents`, `children`. Bei einem der letzten drei erhaelt man eine JSON response mit einer liste (ein eintrag kann mehrere wurzelelemente haben) von objekten mit jeweils `id`, `type` und `name` der verwandten thesauruseintraege. Wenn man `name` oder `type` anfragt, bekommt man eine `text/plain` response wo nur der gewuenschte inhalt drin steht.

### `/ths/search`

- method: `POST`

Man sucht eintraege deren `name` feld mit dem angegebenen `term` beginnen. Das ergebnis ist eine liste von objekten, enthalten im `results`-feld der `application/json`-response. Die einzelnen results enthalten jeweils `id`, `name` und `type`.

Im body koennen/muessen folgende parameter angegeben werden:

|name|range|funktion|default|
|---|---|---|---|
|`term`|mindestens 2 zeichen lang|suchbegriff der im `name` vorkommen soll|**required**|
|`search`|`{prefix\|contains}`|ob `term` am anfang von `name` oder irgendwo steht|`prefix`|
|`limit`|1-50, `int`|wie viele ergebnisse maximal|`50`|
|`type`|einzelner string oder liste von strings|man kriegt nur ergebnisse, deren `type` im parameter genannt ist|

Die ergebnisse werden alphabetisch sortiert nach `name` und auf `limit` oder `50` stueck begrenzt. Beispiel:

```bash
    curl -XPOST -HContent-Type:application/json http://tladev.bbaw.de:5002/ths/search -d '{"term":"h","limit":5}'
```
```json 
{
  "length": 5, 
  "message": "God's in HIS heaven all's right with the earth", 
  "result": [
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
  "status": "success"
}
```

## error handling

Der errorhandler gibt fehlermeldungen in folgender form aus:

```json
{
  "error": {
    "code": 404, 
    "description": "<p>could not find entry with ID TL3NBDJXXZE7RKWNRVQS5TPSB</p>", 
    "name": "Not Found", 
    "type": "NotFound"
  }, 
  "status": "error"
}
```
