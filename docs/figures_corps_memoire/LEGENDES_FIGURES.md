# Figures a placer dans le corps du memoire

| Numero | Fichier | Titre | Source | Commentaire analytique | Donnees simulees ? |
|---|---|---|---|---|---|
| Figure 1 | Figure_01_demarche_recherche.png | Schema global de la demarche de recherche | Elaboration auteur a partir du protocole experimental du projet | La figure relie la problematique, le cadre theorique, les donnees, les experimentations, le prototype et l analyse finale. Elle sert a montrer la coherence entre la recherche academique et la realisation applicative. | Non |
| Figure 2 | Figure_02_desequilibre_classes_ulb.png | Desequilibre des classes du dataset ULB | Dataset ULB creditcard.csv, calcul auteur | La fraude represente 0.173 % des transactions, ce qui justifie le choix de metriques adaptees aux classes rares et l analyse cout/seuil. | Non |
| Figure 3 | Figure_03_pipeline_methodologique.png | Pipeline methodologique supervise anti-fuite temporelle | docs/_empirical_figures/fig2_pipeline_offline.png, elaboration auteur | Le schema explicite l enchainement allant du chargement des donnees jusqu a l evaluation economique, en insistant sur le decoupage temporel pour limiter la fuite d information. | Non |
| Figure 4 | Figure_04_tableau_comparatif_modeles.png | Tableau comparatif final des modeles | reports/tables/model_comparison.csv, calculs experimentaux du projet | Le tableau met en evidence le compromis obtenu par le Random Forest, retenu pour la suite en raison de son equilibre entre precision, rappel, F1, MCC et cout. | Non |
| Figure 5 | Figure_05_precision_recall_comparative.png | Courbe Precision-Recall comparative | reports/figures/21_pr_curves.png | La courbe Precision-Recall est privilegiee car elle reste informative lorsque la classe fraude est tres minoritaire. | Non |
| Figure 6 | Figure_06_matrice_confusion_random_forest.png | Matrice de confusion du modele retenu | reports/figures/22_cm_random_forest.png | La matrice de confusion permet de discuter les faux negatifs, critiques en fraude, et les faux positifs, couteux pour l experience client. | Non |
| Figure 7 | Figure_07_courbe_cout_seuil_harmonisee.png | Courbe cout/seuil harmonisee du Random Forest | reports/tables/cost_analysis_random_forest.csv et cost_comparison_summary.csv | La figure montre pourquoi le seuil standard de 0,50 n est pas necessairement optimal lorsque les faux negatifs et les faux positifs ont des couts asymetriques. | Non |
| Figure 8 | Figure_08_shap_modele_explique.png | Figure SHAP coherente avec le modele explique | Synthese auteur fondee sur le modele Random Forest et les variables expliquees dans le memoire | La figure sert de support interpretable: elle met en avant les variables qui contribuent le plus au score de fraude et rend le modele plus discutable par un lecteur metier. | Partiellement - valeurs SHAP schematisees, pas un export SHAP brut |
| Figure 9 | Figure_09_architecture_prototype.png | Schema d architecture du prototype | docs/_empirical_figures/fig1_architecture.png, elaboration auteur | Le schema montre les deux volets complementaires: apprentissage supervise hors ligne et simulation bancaire temps reel connectee a l API, au stockage et aux tableaux de bord. | Oui pour le volet simulation temps reel ; non pour le volet ULB hors ligne |
| Figure 10 | Figure_10_capture_synthetique_dashboard.png | Capture synthetique du dashboard Power BI | docs/_empirical_figures/fig6_powerbi_pages_map.png, elaboration auteur | Cette capture synthetise les pages Power BI utiles sans surcharger le corps du memoire avec toutes les captures detaillees. | Partiellement : les donnees du module temps reel sont issues de la simulation du prototype |

## Annexes recommandees

Les figures secondaires et techniques ont ete copiees dans `docs/figures_annexes_memoire/` selon les categories suivantes :

- `matrices_confusion_secondaires/` : toutes les matrices de confusion sauf celle du Random Forest retenu.
- `courbes_cout_seuil_autres_modeles/` : courbes cout/seuil des modeles non retenus.
- `courbes_threshold_et_metriques/` : courbes de seuil, FP/FN et gains economiques detaillees.
- `schemas_techniques_lourds/` : scoring dynamique, sequence streaming, modele Power BI en etoile et architecture Docker technique.
- `exports_csv_et_hyperparametres/` : exports CSV et fichiers de synthese disponibles dans `reports/tables/`.

Note : les captures API, Docker, PostgreSQL et payloads WebSocket/SSE ne sont pas toutes disponibles comme fichiers image dans le depot. La capture Docker fournie dans la conversation peut etre conservee en annexe si tu veux documenter l environnement d execution.