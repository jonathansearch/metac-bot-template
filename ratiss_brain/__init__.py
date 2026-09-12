"""ratiss_brain - cerveau custom RATISS Labs pour le bot Metaculus.

Toute la logique custom vit ici (spec FORECASTER-V1, claus rouges R4/R5/R6).
Le fork officiel reste propre pour recevoir les mises a jour upstream.
"""

__all__ = ["SUBMIT_PREDICTIONS", "MAX_QUESTIONS_PER_RUN", "RatissForecastBot"]

from ratiss_brain.config import MAX_QUESTIONS_PER_RUN, SUBMIT_PREDICTIONS
from ratiss_brain.bot import RatissForecastBot
