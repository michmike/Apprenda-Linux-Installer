mkdir apprenda
cd apprenda
mkdir 5.0.Latest
wget https://raw2.github.com/michmike/Apprenda/master/ci-functions 
wget https://raw2.github.com/michmike/Apprenda/master/ci-init-bootstrap.sh 
wget https://raw2.github.com/michmike/Apprenda/master/ci-java-prereqs.sh 
wget https://raw2.github.com/michmike/Apprenda/master/5.0.Latest/argparse.py
wget https://raw2.github.com/michmike/Apprenda/master/5.0.Latest/hostconfig.py 
wget https://raw2.github.com/michmike/Apprenda/master/5.0.Latest/prereqChecker.py 
mv argparse.py 5.0.Latest\
mv prereqChecker.py 5.0.Latest\
mv hostconfig.py 5.0.Latest\
chmod +x ./ci-functions
chmod +x ./ci-init-bootstrap.sh
./ci-init-bootstrap.sh
chmod +x ./ci-java-prereqs.sh
./ci-java-prereqs.sh
./ci-java-prereqs.sh '5.0.Latest'
