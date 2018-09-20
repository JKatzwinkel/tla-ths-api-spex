# tla-ths-api-spex
wie man thesauruseintraege des berliner altaegyptischen woerterbuches abrufen und suchen soll

## endpunkte

### `/ths/get/<string:id>`

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

Man gibt zusaetzlich zur 24-stelligen ID noch den namen der eigenschaft an, die man haben will. Moeglich sind `name`, `type`, `root`, `parents`, `children`. Bei letzteren drei erhaelt man eine JSON response mit einer liste (ein eintrag kann mehrere wurzelelemente haben) von objekten mit jeweils `id` und `name` der verwandten thesauruseintraege. Wenn man `name` oder `type` anfragt, bekommt man eine `text/html` response wo nur der gewuenschte inhalt drin steht.

