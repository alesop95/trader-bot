# Configurazione di latexmk per una build riproducibile (sezione 13).
# Fissa l'engine a pdflatex come dichiarato nel preambolo del .tex, abilita SyncTeX
# (per il jump editor<->PDF) e una modalita' non interattiva che non si blocca sugli errori.
# Questo file viene letto automaticamente da latexmk quando eseguito nella radice del progetto.

$pdf_mode = 1;   # 1 = pdflatex (non lualatex/xelatex)
$pdflatex = 'pdflatex -interaction=nonstopmode -halt-on-error -synctex=1 -file-line-error %O %S';

# Estensioni ausiliarie da rimuovere con `latexmk -c` / `-C` (coerenti col .gitignore).
$clean_ext = 'synctex.gz aux fdb_latexmk fls run.xml bcf nav snm vrb out toc lof lot';
