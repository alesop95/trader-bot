# Profilo del learner

> Scaffold vuoto del pacchetto `learning-agent` (vedi `.claude/context/learning-agent-reference.md`, sezione 6). Popolato dalla skill `build-roadmap` alla prima esecuzione di `/profile`, e riletto e aggiornato da `tutor` a ogni sessione di `/learn` e `/review`. È la fonte di verità dello stato di apprendimento: non si modifica a mano se non per correggere un errore, perché gli agenti del pacchetto lo trattano come stato affidabile.

```yaml
topic: null
category: null          # language | programming | conceptual
level: null              # beginner | intermediate | advanced
session_minutes: null
cadence: null
kb_mcp: none             # nome del server MCP di knowledge base connesso, o "none"
anki_mcp: none           # nome del server MCP Anki connesso, o "none"
cognitive_profile:
  adhd: false
  autism: false
  dyslexia: false
style: []                # visual | textual | hands_on
special_interests: []
progress:
  roadmap_module: null
  anki_deck: null
```

## Roadmap

<popolata da build-roadmap secondo il template pedagogico della categoria dichiarata sopra: elenco di moduli o unità, con le dipendenze tra moduli se la categoria è programming>
