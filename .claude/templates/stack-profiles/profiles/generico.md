# Profilo di stack: generico

> Regola modulare istanziata dal pacchetto `stack-profiles` come `stack-profile.md`. È il fallback esplicito per i progetti il cui stack non ha un profilo dedicato.

Nessuna convenzione specifica di stack è imposta. Si seguono le convenzioni rilevate nel codebase, e man mano che emergono si documentano nella scheda `context/STACK.md`, oppure direttamente in questo file quando diventano prescrittive, trasformandolo gradualmente nel profilo su misura del progetto. Se col tempo il progetto converge su uno stack che ha un profilo dedicato nel pacchetto `stack-profiles`, si valuta di sostituire questo file con quel profilo, riportandovi le convenzioni già accumulate.
