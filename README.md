# boobank_virement_cragr

**Récupération de l'historique**
- installer boobank (inclus dans la v1.0 de weboob: http://weboob.org/applications/boobank)
- il faut tout d'abord appliquer un fix à la main (cf https://symlink.me/issues/2244 et https://git.symlink.me/?p=kitof/weboob.git;a=commitdiff;h=45f70cbe5b7cd3405dd4e9fcd0e5cd6cec277683)
- lancer boobank (boobank<enter>)
Il nous est alors proposé d'ajouter des backends (banques)
- Saisir 'Y', Saisir 20 ('cragr' pour le crédit agricole)
- Saisir '5' pour le crédit agricole atlantique vendée
- Saisir 'S' pour le stockage des paramètres dans un fichier de config (pour info fichier ~/.config/weboob/backends)
- Saisir le numéro de compte
- Saisir 'S' à nouveau
- Saisir le mot de passe du compte (mot de passe utilisé pour accéder au compte via l'interface web de la banque)
- Saisir 'q' pour quitter la configuration de backends
- Quitter boobank
Désormais on peut accéder aux informations du compte via une ligne de commande
Par exemple, 'boobank history 73941722595@cragr' renverra l'historique des transactions du compte.
On peut ensuite ajouter des conditions et des filtres.
Par exemple 'boobank history 73941722595@cragr -c 'category|Prelev AND date>2015-11-27' -f csv > export.csv' filtrera les opérations dont le nom commence par 'Prelev' et dont la date est supérieure au 27/11/2015. Le résultat sera stocké dans le fichier 'export.csv'




**Effectuer des transferts de compte à compte**

Le transfert n'est pas implémenté dans le module crédit agricole cragr.
Pour cela il faut modifier 4 fichiers:
modules/cragr/module.py
modules/cragr/web/browser.py
modules/cragr/web/pages.py
weboob/applications/boobank/boobank.py

J'ai joint le diff des fichiers (versus la v1.0 de weboob) et les 4 fichiers modifiés.

Les 3 fichiers dans le répertoire "module/cragr" seront pris en compte directement.
Le fichier boobank.py devra être modifié dans le répertoire d'exécution de boobank (dans mon cas: ~/Library/Python/2.7/lib/python/site-packages/weboob-1.0-py2.7.egg/weboob/applications/boobank) et compilé " sudo python -m compileall boobank.py".

Pour effectuer un transfert il faut exécuter: "boobank transfer 73941722595@cragr BE48001672835627 11 'test'"
Cela fera un virement de 11 euros du compte 73941722595 vers le compte BE48001672835627 (iban du compte) et le libellé du transfert sera "test".

Pour effectuer ce virement, boobank utilise selenium et le webdriver firefox.
Pour l'exécuter sur un serveur, il faudra utiliser une version headless de firefox.
Ce lien (http://scraping.pro/use-headless-firefox-scraping-linux/) explique comment l'installer et l'utiliser. Il y aura 2/3 lignes à ajouter dans le fichier modules/cragr/web/browser.py
