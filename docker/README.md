Etapes suivies pour tester cette installation
- installation d'ubuntu (ubuntu-16.04-desktop-amd64.iso) sur une VM 
- installation de docker en suivant à la lettre cette procédure https://docs.docker.com/engine/installation/linux/ubuntulinux/
- ajout de mon user dans le groupe docker: sudo usermod -aG docker ${whoami}
- log out ubuntu
- log in ubuntu
- lancement de docker via: source run.sh

Important pour le bon fonctionnement du virement, le compte destinataire du virement (BOOBANK_CPT2) doit faire partie des comptes bénéficiaires enregistrés sur le compte émetteur (BOOBANK_CPT1). L'ajout de compte bénéficiaire (si nécessaire) doit se faire via l'interface web du compte bancaire ou en demandant directement à la banque.
