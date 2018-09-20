# tla-ths-api-spex
wie man thesauruseintraege des berliner altaegyptischen woerterbuches abrufen und suchen soll

## endpunkte

### `/ths/get/<string:id>`

- method: `GET`

Man gibt die 24-stellige ID des thesauruseintrags an und bekommt eine `application/json` response folgender art:

    {
      "children": [],
      "id": "CLJN6LLO5NDL7DY6HOP4XC4ELE",
      "name": "Butler, Cuthbert",
      "parents": [
        "OJDRAHAIX5BMND7OQH3TKTG4C4"
      ],
      "type": "person"
    }
    
    
### `/ths/get/<string:id>/<string:key>`

- method: `GET`

Man gibt zusaetzlich zur 24-stelligen ID noch den namen der eigenschaft an, die man haben will. Moeglich sind `name`, `type`, `root`, `parents`, `children`. Bei letzteren drei erhaelt man eine JSON response mit einer liste (ein eintrag kann mehrere wurzelelemente haben) von objekten mit jeweils `id` und `name` der verwandten thesauruseintraege. Wenn man `name` oder `type` anfragt, bekommt man eine `text/html` response wo nur der gewuenschte inhalt drin steht.

### `/ths/find/prefix/<string:prefix>`

- method: `GET`

Man sucht eintraege deren `name` feld mit dem angegebenen `prefix` beginnen. Das ergebnis ist eine liste von objekten als `application/json`. Die einzelnen objekte der response enthalten jeweils `id`, `name` und `type` der einzelergebnisse.

Die ergebnisse werden alphabetisch sortiert nach `name` und auf `50` stueck begrenzt. Beispiel:

    -XGET http://tladev.bbaw.de:5002/ths/find/prefix/h
    [
        {
            "type": "location",
            "id": "7QGME3V2XZDN3IJKDWHZJWHEWU",
            "name": "Haags Gemeentemuseum"
        },
        {
            "type": "material",
            "id": "IX35XEUNPNFBNDU4UNB4CQRTXA",
            "name": "Haar"
        },
        {
            "type": "objecttype",
            "id": "3MMFFLHZI5F4DHBJTX2Q7PI3JA",
            "name": "Haarkranz"
        },
        {
            "type": "bibliography",
            "id": "W6EYN4YCLBEV7JGI5JVHLPKRL4",
            "name": "Habachi, Heqaib"
        ...

### `/ths/find/prefix/<string:type>/<string:prefix>`

- method: GET

Man sucht eintraege mit einem bestimmten `type`, deren `name` mit dem angegebenen prefix beginnen. Ansonsten gelten dieselben bedingungen wie bei der [normalen prefix-suche](#thsfindprefixstringprefix).

Beispiel: 

    -XGET http://tladev.bbaw.de:5002/ths/find/prefix/location/saqqara
    [
        {
            "type": "location",
            "name": "Saqqara",
            "id": "T66IQ2R26NHZTMIVAS7SVLRWGI"
        }
    ]
