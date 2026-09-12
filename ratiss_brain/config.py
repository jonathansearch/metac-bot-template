"""Config verrouillee - spec FORECASTER-V1, regles rouges.

- R1 : submit_predictions=False partout tant que le go-live n'est pas signe.
- R3 : plafond d'appels LLM par run: 200 questions max, code en dur.
Ne jamais lire ces valeurs depuis l'environnement - elles sont la garde-fou du run.

"""


# R1 - go-live verrouille. Le passage a True exige: backtest rouge OK ET signature ecrite
#de Jonathan dans SPEC-FORECASTER-V1.md. Valeur lue UNIQUEMENT ici (jamais dans les appels).

SUBMIT_PREDICTIONS: bool = False

# R3 - budget garde-fou: plafond d'appels LLM par run (questions), code en dur.

MAX_QUESTIONS_PER_RUN:int = 200

# R6 - volet P_sig experimental. OFF par defaut:la voie A (bot principal) doit marcher
#a 100 % avec le module desactive,et aucune dependance A->B n'existe.


TOPOLOGY_PROBE_ENABLED: bool = False
