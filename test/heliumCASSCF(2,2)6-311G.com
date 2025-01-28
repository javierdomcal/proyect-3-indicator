%chk=heliumCASSCF(2,2)6-311G.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(2,2)/6-311G gfinput fchk=all density=current iop(4/21=100) 

heliumCASSCF(2,2)6-311G helium CASSCF(2,2) 6-311G

0 1
He    0.0000   0.0000   0.0000

