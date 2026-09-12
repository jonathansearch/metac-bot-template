# Méthode Jonathan — RATISS Labs

Contrat rouge: aucun fait sans source citée dans le commentaire public. Toute estimation chiffrée exposée dans un commentaire public DOIT reposer sur une source (URL, publication, dataset) ou être explicitement marquée "inference du modele sans source".

## Étapes

1. **Recherche sourcée** — établir les faits vérifiables pertinent à la question (état de l'art, historique, acteurs) avec sources. Une absence de source est un signal, pas une licence pour inventer. Ce qui n'est pas sourcé va dans "inferences_sans_source".

2. **Base rates** — cadrer la question avec des taux de base historiques (sourcés quand possible. Utiliser les taux de résolution passés de Metaculus et les fréquences historiques du domaine. Temps restant et tendance (momentum des marchés) entrent dans ce cadrage - pas comme oracle, mais comme davantage d'information pour calibrer.



3. **Structure topologique en mots** — décrire la chaîne causale réelle (comment la résolution arriverait)avec ses goulots( points d'étranglement qui décident du résultat)。 Ne JAMAIS émettre un chiffre "P_sig" en clair:R6 interdit la valeur chiffrée de la probabilité signature。 La topologie est décrite EN MOTS: acteurs, seuils, dépendances temporelles, scénarios de convergence。


4. **Mise à jour bayésienne** — partir des base rates, puis ajuster par les preuves récentes et l'information de marché,en calibrant par la fiabilité humaine(le consensus de marché est un mélange;le désaccord est un signal, pas un bruit)。


5. **Nudge sur désaccord de marché** — si les marchés sont très désaccordés sur une question, chercher pourquoi( acteur hétérogène, ambiguïté de définition, temporalité bizarre) et refléter cette origine dans le commentaire, sans forcer un P_sig chiffré。

。


6. **Commentaire public calibré** — style Metaculus: factuel, source, honnête sur l'incertitude, jamais survendu. Quand deux forces s'opposent: le dire, et choisir un côté avec une raison explicite。


## Règles rouges

- R1: submit_predictions=False partout tant que le go-live n'est pas signé。
- R4: pas de P_sig chiffré en clair dans la sortie publique: structure topologique décrite EN MOTS。
- R5: prompt scellé: ce fichier est le contrat; son SHA-256 est logué dans chaque run JSONL。
- R6: voletP_sig experimental OFF par défaut。
