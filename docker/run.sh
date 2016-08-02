echo "usage: source run.sh"
echo "Il faut précédé la commande de 'source' à cause d'affectations de variables d'environnement."

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo $DIR

cd $DIR

if [ -z ${BOOBANK_SITE+x} ]; then unset BOOBANK_CPT1; unset BOOBANK_CPT1_PASS; unset BOOBANK_CPT2; echo "Saisir le site de la caisse (ex: m.ca-atlantique-vendee.fr): "; read BOOBANK_SITE; fi
export BOOBANK_SITE

if [ -z ${BOOBANK_CPT1+x} ]; then echo "Saisir le numero de compte (ex: 73xxxxxxx48): "; read BOOBANK_CPT1; fi
export BOOBANK_CPT1

if [ -z ${BOOBANK_CPT1_PASS+x} ]; then echo "Saisir le mot de pass du compte $BOOBANK_CPT1: "; read BOOBANK_CPT1_PASS; fi
export BOOBANK_CPT1_PASS

if [ -z ${BOOBANK_CPT2+x} ]; then echo "Saisir le numero de compte de la destination du transfer (ex: FR76xxxxxxxxxxxxxxxxxxxxx97): "; read BOOBANK_CPT2; fi
export BOOBANK_CPT2

sudo rm -r data-boobank

docker build --build-arg BOOBANK_SITE=${BOOBANK_SITE} --build-arg BOOBANK_CPT1=${BOOBANK_CPT1} --build-arg BOOBANK_CPT1_PASS=${BOOBANK_CPT1_PASS} -t wb .

# Affichage de l'historique du compte.
docker run wb boobank history ${BOOBANK_CPT1}@cragr

# Transfer
docker run wb /bin/bash -c "boobank --debug transfer ${BOOBANK_CPT1}@cragr ${BOOBANK_CPT2} 1 'test virement 1 euro'"
