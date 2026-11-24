# Ultimo allineamento dal template

<!-- generato da allinea-dal-template.py -->

Commit a monte: `99b13ffc66bf1b78a067f9adebe007b3af546df4`. File interessati dalla passata: 23. Commit e push del progetto restano manuali.

| Esito | File |
|---|---|
| VECCHIO | `.claude/rules/git-commands-format.md` |
| NUOVO | `.claude/skills/progetti-su-vm/RIFERIMENTO.md` |
| NUOVO | `.claude/skills/progetti-su-vm/SKILL.md` |
| VECCHIO | `.claude/templates/CLAUDE.md` |
| VECCHIO | `.claude/templates/agenti-terminale/README.md` |
| NUOVO | `.claude/templates/agenti-terminale/recupero-dopo-crash.md` |
| VECCHIO | `.claude/templates/agenti-terminale/rules/chiusura-delle-sessioni.md` |
| NUOVO | `.claude/templates/agenti-terminale/tests/test-pulisci-codex-quarantena.ps1` |
| VECCHIO | `.claude/templates/agenti-terminale/tools/Avvia-Claude.ps1` |
| VECCHIO | `.claude/templates/agenti-terminale/tools/Avvia-Codex.ps1` |
| VECCHIO | `.claude/templates/agenti-terminale/tools/Pulisci-Codex.ps1` |
| NUOVO | `.claude/templates/agenti-terminale/tools/Recupera-DaShadow.ps1` |
| NUOVO | `.claude/templates/agenti-terminale/tools/Riapri-Sessione.ps1` |
| VECCHIO | `.claude/templates/fonti-a-monte.json` |
| VECCHIO | `.claude/templates/lezioni-recepite.json` |
| VECCHIO | `.claude/templates/riferimento-voci.json` |
| VECCHIO | `.claude/templates/tools/allinea-dal-template.py` |
| VECCHIO | `.claude/templates/tools/guida-grafica.py` |
| VECCHIO | `.claude/templates/tools/identita-forme-ammesse.txt` |
| VECCHIO | `.claude/templates/tools/session-end-wipe.ps1` |
| VECCHIO | `.claude/templates/tools/test-identita-personali.py` |
| VECCHIO | `.claude/templates/tools/tests/test-wipe-per-sessione.ps1` |
| INNESCO | `CLAUDE.md` |

Conflitti ancora da risolvere: 0.

## Gate dei pacchetti

Gate dovuto: 107 voci del catalogo su 107 non sono mai state viste dal gate né decise (nessuna tornata registrata). La tornata la avvia /riprendi, oppure /gate-pacchetti.

La riga si ricalcola in ogni momento con `python .claude/templates/tools/verifica-pacchetti.py --gate`. Una tornata dovuta si dice al proprietario nella prima risposta della sessione, perché l'agente non può lanciare `/gate-pacchetti` da sé.

Voci mai viste: `academic-researcher`, `academix`, `agent-catalog`, `agenti-terminale`, `alignment`, `anatomy`, `andrej-karpathy-skills`, `anki-mcp`, `anonymization`, `anti-slop`, `arxiv-cli`, `automation-starter`, `blender-skills`, `book-bib-extract`, `book-to-skill`, `caveman`, `ccusage`, `claude-code-handoff`, `claude-code-router`, `claude-mem`, `code-context`, `code-simplifier`, `codebase-learning`, `codebase-memory-mcp`, `comandi-ragionamento`, `community-sources`, `context-mode`, `context7`, `craft-apps`, `cyber-lab`, `deepwiki-mcp`, `deepwiki-skill`, `dev-skills`, `diagram-design`, `diagrams`, `discord-mcp`, `doc-ingest`, `documentazione-didattica`, `docx-to-docs`, `drawio-skill`, `feynman`, `figma-mcp`, `fix-typography`, `gancio-globale`, `github-mcp`, `graphify`, `grc-skills`, `grobid`, `guardia-pubblicazione`, `hallmark`, `headroom`, `hermes-agent`, `hooks-starter`, `humanizer`, `impeccable`, `instradamento-modelli`, `knowledge-mcp`, `knowledge-wiki`, `latex`, `lavoro-a-lotti`, `learning-agent`, `linear-mcp`, `llm-local`, `matt-pocock-skills`, `md-unwrap`, `memoria-di-progetto`, `micro-passi`, `mods-claude-code`, `multiclaude`, `nimbalyst`, `notebooklm-bridge`, `openalex`, `operations-log`, `paperqa2`, `pipeline-app`, `playwright-mcp`, `ponytail`, `psmux`, `rea`, `readme-sync`, `refchecker-mcp`, `repomix`, `roadmap`, `rtk`, `scientific-skills`, `security-audit`, `semantic-scholar-mcp`, `sentry-mcp`, `separazione-ambienti`, `serena`, `stack-profiles`, `stratega-impresa`, `subagent-template`, `superpowers`, `taste-skill`, `timeline-progetto`, `tmux-claude-hatch`, `vault-di-progetto`, `veeam-linux`, `vercel-mcp`, `verifica-link`, `voicestudio`, `voicestudio-mcp`, `voltagent-subagents`, `vps-baseline`, `wshobson-agents`, `zotero-mcp`.
