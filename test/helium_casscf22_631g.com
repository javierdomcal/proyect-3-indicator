%chk=test/helium_casscf22_631g.chk
%mem=2GB
%NProcShared=1
#P SP CASSCF(2,2)/6-31G density=current gfinput fchk=all out=wfx iop(9/40=7) iop(9/28=-1) use=l916

helium CASSCF(2,2) Calculation helium CASSCF(2,2) 6-31G

0 1
He    0.0000   0.0000   0.0000

test/helium_casscf22_631g.wfx

